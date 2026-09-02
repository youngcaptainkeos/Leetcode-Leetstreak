import os
import logging
import secrets
import string
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Set

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS, ADMIN_SECRET
from .database import Base, engine, get_db, SessionLocal
from .models import User, DailyActivity, Group, GroupMember, Solve, Kudos
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from .email_service import send_otp_email
from .schemas import (
    RegisterRequest, RegisterResponse, DashboardResponse, DayCount,
    LeaderboardResponse, LeaderboardEntry, GroupCreateRequest, GroupJoinRequest,
    GroupResponse, GroupListResponse, GroupMemberSchema, RecentSolveSchema,
    LoginRequest, ForgotPasswordInitiateRequest, ForgotPasswordVerifyRequest,
    KudosToggleRequest, UpdateUsernameRequest, ActivityFeedItemSchema,
    DynamicMenuItem, AppConfigResponse,
)
from .streak import current_streak
from .scheduler import start_scheduler, poll_all_users, poll_user
from .leetcode_client import fetch_leetcode_user_data, LeetCodeError


def verify_admin_secret(x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret")):
    if ADMIN_SECRET and x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Secret Header")
    return True

from sqlalchemy import text, func

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

# Safe auto-migration for existing PostgreSQL/SQLite tables
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(120);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(200);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;"))
        # Drop unique constraint on leetcode_username if present
        conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_leetcode_username_key;"))
        conn.execute(text("DROP INDEX IF EXISTS ix_users_leetcode_username;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_leetcode_username ON users (leetcode_username);"))
        conn.commit()
except Exception as migration_err:
    logging.warning("Auto-migration executed: %s", migration_err)

app = FastAPI(title="LeetStreak API")

origins = ["*"] if CORS_ORIGINS.strip() == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scheduler = None


@app.on_event("startup")
async def on_startup():
    global _scheduler
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_leetcode_username_key;"))
            conn.execute(text("CREATE TABLE IF NOT EXISTS kudos (id SERIAL PRIMARY KEY, from_user_id INTEGER NOT NULL, to_user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"))
    except Exception as e:
        logger.warning("Startup table migration warning: %s", e)

    db = SessionLocal()
    try:
        # Initialize created_at for any existing users if null
        existing_users_without_date = db.query(User).filter(User.created_at.is_(None)).all()
        for u in existing_users_without_date:
            u.created_at = datetime.now()

        bloated_rows = db.query(DailyActivity).filter(DailyActivity.problems_solved > 1).all()
        for r in bloated_rows:
            solves_count = db.query(Solve).filter(
                Solve.user_id == r.user_id,
                func.date(Solve.solved_at) == r.date
            ).count()
            r.problems_solved = max(1, solves_count)
        db.commit()
    except Exception as e:
        logger.warning("Startup activity cleanup failed: %s", e)
        db.rollback()
    finally:
        db.close()

    _scheduler = start_scheduler()


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _generate_group_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "STREAK-" + "".join(secrets.choice(chars) for _ in range(length))


@app.post("/api/users/register", response_model=RegisterResponse)
async def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        data = await fetch_leetcode_user_data(payload.leetcode_username)
    except LeetCodeError as err:
        raise HTTPException(
            status_code=400,
            detail=str(err),
        )

    clean_email = payload.email.strip().lower()
    existing_email_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_email_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email is already registered. Please log in instead.",
        )

    canonical_username = data.get("username", payload.leetcode_username)

    user = User(
        name=payload.name,
        leetcode_username=canonical_username,
        email=clean_email,
        password_hash=hash_password(payload.password),
        avatar_url=data.get("avatar_url"),
        created_at=datetime.now(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email is already registered.")
    db.refresh(user)

    # Ingest full history
    await poll_user(db, user)

    token = create_access_token(user.id)
    return RegisterResponse(
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        avatar_url=user.avatar_url,
        access_token=token,
        token_type="bearer",
        created_at=user.created_at,
    )


@app.post("/api/users/login", response_model=RegisterResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    query_str = payload.leetcode_username.strip().lower()
    matching_users = (
        db.query(User)
        .filter((func.lower(User.email) == query_str) | (func.lower(User.leetcode_username) == query_str))
        .all()
    )

    matched_user = None
    for u in matching_users:
        if u.password_hash and verify_password(payload.password, u.password_hash):
            matched_user = u
            break

    if not matched_user:
        raise HTTPException(status_code=400, detail="Invalid username/email or password.")

    token = create_access_token(matched_user.id)
    return RegisterResponse(
        id=matched_user.id,
        name=matched_user.name,
        leetcode_username=matched_user.leetcode_username,
        avatar_url=matched_user.avatar_url,
        access_token=token,
        token_type="bearer",
        created_at=matched_user.created_at,
    )


@app.post("/api/users/forgot-password/initiate")
async def initiate_forgot_password(payload: ForgotPasswordInitiateRequest, db: Session = Depends(get_db)):
    query_str = payload.email_or_username.strip().lower()
    user = (
        db.query(User)
        .filter((func.lower(User.leetcode_username) == query_str) | (func.lower(User.email) == query_str))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that email or username.")

    if not user.email:
        raise HTTPException(status_code=400, detail="This account does not have an email address associated with it.")

    otp_code = "".join(secrets.choice(string.digits) for _ in range(6))
    user.reset_otp = otp_code
    user.otp_expires_at = datetime.now() + timedelta(minutes=15)
    db.commit()

    await send_otp_email(user.email, user.leetcode_username, otp_code)
    return {"status": "otp_sent", "email": user.email}


@app.post("/api/users/forgot-password/verify")
def verify_forgot_password(payload: ForgotPasswordVerifyRequest, db: Session = Depends(get_db)):
    query_str = payload.email_or_username.strip().lower()
    user = (
        db.query(User)
        .filter((func.lower(User.leetcode_username) == query_str) | (func.lower(User.email) == query_str))
        .first()
    )
    if not user or user.reset_otp != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid or incorrect 6-digit OTP code.")

    if not user.otp_expires_at or user.otp_expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="OTP code has expired. Please request a new code.")

    user.password_hash = hash_password(payload.new_password)
    user.reset_otp = None
    user.otp_expires_at = None
    db.commit()

    return {"status": "password_reset_success"}


@app.post("/api/users/{user_id}/sync")
async def sync_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    solves_added = await poll_user(db, user)
    return {"status": "synced", "user_id": user_id, "new_solves": solves_added}


@app.put("/api/users/{user_id}/leetcode-username")
async def update_leetcode_username(user_id: int, payload: UpdateUsernameRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_username = payload.leetcode_username.strip()
    if not new_username:
        raise HTTPException(status_code=400, detail="LeetCode username cannot be empty.")

    try:
        data = await fetch_leetcode_user_data(new_username)
    except LeetCodeError as err:
        raise HTTPException(status_code=400, detail=str(err))

    user.leetcode_username = new_username
    user.avatar_url = data.get("avatar_url")
    db.commit()

    await poll_user(db, user)

    return {
        "status": "username_updated",
        "user_id": user_id,
        "leetcode_username": user.leetcode_username,
        "avatar_url": user.avatar_url,
    }


def _active_dates(db: Session, user_id: int) -> set[date]:
    rows = (
        db.query(DailyActivity.date)
        .filter(DailyActivity.user_id == user_id, DailyActivity.problems_solved > 0)
        .all()
    )
    return {r[0] for r in rows}


IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_today() -> date:
    """Returns today's date in Indian Standard Time (IST, UTC+5:30)."""
    return datetime.now(IST).date()


def get_current_week_start(today: date) -> date:
    """Returns Sunday 00:00:00 (start of current week). Resets weekly counter every Sunday 12:00 AM."""
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def get_current_month_start(today: date) -> date:
    """Returns 1st of the current calendar month 00:00:00. Resets monthly counter on the 1st of every month."""
    return date(today.year, today.month, 1)


def get_ist_today_start() -> datetime:
    """Returns midnight (00:00:00) of current calendar day in Indian Standard Time (IST, UTC+5:30) converted to naive UTC for DB comparison."""
    now_ist = datetime.now(IST)
    midnight_ist = datetime(now_ist.year, now_ist.month, now_ist.day)
    utc_midnight = midnight_ist - timedelta(hours=5, minutes=30)
    return utc_midnight.replace(tzinfo=None)


@app.get("/api/users/{user_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = get_ist_today()
    week_start = get_current_week_start(today)
    month_start = get_current_month_start(today)

    active_dates = _active_dates(db, user_id)
    streak = current_streak(active_dates, today)

    def total_since_date(start_date: date) -> int:
        rows = (
            db.query(DailyActivity)
            .filter(DailyActivity.user_id == user_id, DailyActivity.date >= start_date)
            .all()
        )
        return sum(r.problems_solved for r in rows)

    last_7 = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        row = (
            db.query(DailyActivity)
            .filter(DailyActivity.user_id == user_id, DailyActivity.date == d)
            .first()
        )
        last_7.append(DayCount(date=d, problems_solved=row.problems_solved if row else 0))

    today_row = next((d for d in last_7 if d.date == today), None)

    return DashboardResponse(
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        avatar_url=user.avatar_url,
        easy_count=user.easy_count or 0,
        medium_count=user.medium_count or 0,
        hard_count=user.hard_count or 0,
        current_streak=streak,
        today_count=today_row.problems_solved if today_row else 0,
        weekly_total=total_since_date(week_start),
        monthly_total=total_since_date(month_start),
        created_at=user.created_at,
        last_7_days=last_7,
    )


def _compute_leaderboard(
    db: Session,
    users: List[User],
    requester_id: Optional[int] = None,
    sort_by: str = "points",
    limit: Optional[int] = None,
) -> LeaderboardResponse:
    today = get_ist_today()
    week_start = get_current_week_start(today)
    days_in_week_so_far = (today - week_start).days + 1
    cutoff_today = get_ist_today_start()

    # Pre-fetch today's active kudos (IST calendar day)
    active_kudos = db.query(Kudos).filter(Kudos.created_at >= cutoff_today).all()
    kudos_counts = {}
    requester_kudosed_to = set()

    for k in active_kudos:
        kudos_counts[k.to_user_id] = kudos_counts.get(k.to_user_id, 0) + 1
        if requester_id and k.from_user_id == requester_id:
            requester_kudosed_to.add(k.to_user_id)

    user_ids = [u.id for u in users]
    if not user_ids:
        return LeaderboardResponse(week_start=week_start, week_end=today, entries=[])

    # Single batch query for daily activity of all target users
    user_activities = (
        db.query(DailyActivity)
        .filter(DailyActivity.user_id.in_(user_ids), DailyActivity.problems_solved > 0)
        .all()
    )

    active_dates_map: Dict[int, Set[date]] = defaultdict(set)
    week_rows_map: Dict[int, List[DailyActivity]] = defaultdict(list)

    for act in user_activities:
        active_dates_map[act.user_id].add(act.date)
        if act.date >= week_start:
            week_rows_map[act.user_id].append(act)

    raw = []
    for user in users:
        active_dates = active_dates_map[user.id]
        streak = current_streak(active_dates, today)
        week_rows = week_rows_map[user.id]
        weekly_total = sum(r.problems_solved for r in week_rows)
        active_days_this_week = len(week_rows)
        consistency = (active_days_this_week / days_in_week_so_far) * 100
        is_active_today = today in active_dates
        points = ((user.easy_count or 0) * 1) + ((user.medium_count or 0) * 3) + ((user.hard_count or 0) * 6)
        raw.append({
            "user": user,
            "weekly_total": weekly_total,
            "streak": streak,
            "consistency": consistency,
            "points": points,
            "is_active_today": is_active_today,
            "kudos_count": kudos_counts.get(user.id, 0),
            "has_kudosed": user.id in requester_kudosed_to,
        })

    max_weekly = max((r["weekly_total"] for r in raw), default=0) or 1
    for r in raw:
        normalized_volume = (r["weekly_total"] / max_weekly) * 100
        r["combined"] = round(0.6 * r["consistency"] + 0.4 * normalized_volume, 1)

    if sort_by == "streak":
        raw.sort(key=lambda r: (r["streak"], r["points"], r["combined"]), reverse=True)
    else:
        raw.sort(key=lambda r: (r["points"], r["combined"], r["streak"]), reverse=True)

    entries = [
        LeaderboardEntry(
            rank=i + 1,
            id=r["user"].id,
            name=r["user"].name,
            leetcode_username=r["user"].leetcode_username,
            avatar_url=r["user"].avatar_url,
            easy_count=r["user"].easy_count or 0,
            medium_count=r["user"].medium_count or 0,
            hard_count=r["user"].hard_count or 0,
            points=r["points"],
            weekly_total=r["weekly_total"],
            current_streak=r["streak"],
            consistency_score=round(r["consistency"], 1),
            combined_score=r["combined"],
            is_active_today=r["is_active_today"],
            kudos_count=r["kudos_count"],
            has_kudosed=r["has_kudosed"],
        )
        for i, r in enumerate(raw)
    ]

    # Top Limit + User Rank Pinning
    if limit is not None and len(entries) > limit:
        top_entries = entries[:limit]
        if requester_id is not None:
            user_in_top = any(e.id == requester_id for e in top_entries)
            if not user_in_top:
                requester_entry = next((e for e in entries if e.id == requester_id), None)
                if requester_entry:
                    top_entries.append(requester_entry)
        entries = top_entries

    return LeaderboardResponse(week_start=week_start, week_end=today, entries=entries)


@app.get("/api/leaderboard", response_model=LeaderboardResponse)
def get_global_leaderboard(
    user_id: Optional[int] = Query(None),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Global Leaderboard includes all registered users on the platform
    users = db.query(User).all()
    return _compute_leaderboard(db, users, requester_id=user_id, sort_by=sort_by, limit=limit)


@app.get("/api/friends/leaderboard", response_model=LeaderboardResponse)
def get_friends_leaderboard(
    user_id: int = Query(...),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Aggregated leaderboard of all unique friends who share at least one group with user_id
    my_group_ids = [
        m.group_id for m in db.query(GroupMember.group_id).filter(GroupMember.user_id == user_id).all()
    ]
    if not my_group_ids:
        friends = db.query(User).filter(User.id == user_id).all()
    else:
        friend_user_ids = [
            m.user_id for m in db.query(GroupMember.user_id).filter(GroupMember.group_id.in_(my_group_ids)).all()
        ]
        friends = db.query(User).filter(User.id.in_(set(friend_user_ids))).all()

    return _compute_leaderboard(db, friends, requester_id=user_id, sort_by=sort_by, limit=limit)


# Group Endpoints
@app.post("/api/groups", response_model=GroupResponse)
def create_group(payload: GroupCreateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = _generate_group_code()
    group = Group(name=payload.name, code=code, creator_id=user.id)
    db.add(group)
    db.commit()
    db.refresh(group)

    membership = GroupMember(group_id=group.id, user_id=user.id)
    db.add(membership)
    db.commit()

    return GroupResponse(
        id=group.id,
        name=group.name,
        code=group.code,
        creator_id=group.creator_id,
        member_count=1,
        members=[
            GroupMemberSchema(
                id=user.id,
                name=user.name,
                leetcode_username=user.leetcode_username,
                avatar_url=user.avatar_url,
            )
        ],
    )


@app.post("/api/groups/join", response_model=GroupResponse)
def join_group(payload: GroupJoinRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code_clean = payload.code.strip().upper()
    group = db.query(Group).filter(Group.code == code_clean).first()
    if not group:
        raise HTTPException(status_code=404, detail="Invalid group code. Please check the code and try again.")

    existing_mem = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
        .first()
    )
    if not existing_mem:
        db.add(GroupMember(group_id=group.id, user_id=user.id))
        db.commit()

    members = (
        db.query(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group.id)
        .all()
    )

    return GroupResponse(
        id=group.id,
        name=group.name,
        code=group.code,
        creator_id=group.creator_id,
        member_count=len(members),
        members=[
            GroupMemberSchema(
                id=m.id,
                name=m.name,
                leetcode_username=m.leetcode_username,
                avatar_url=m.avatar_url,
            )
            for m in members
        ],
    )


@app.get("/api/groups/my-groups/{user_id}", response_model=GroupListResponse)
def get_my_groups(user_id: int, db: Session = Depends(get_db)):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
    group_responses = []

    for mem in memberships:
        group = db.query(Group).filter(Group.id == mem.group_id).first()
        if not group:
            continue
        m_users = (
            db.query(User)
            .join(GroupMember, GroupMember.user_id == User.id)
            .filter(GroupMember.group_id == group.id)
            .all()
        )
        group_responses.append(
            GroupResponse(
                id=group.id,
                name=group.name,
                code=group.code,
                creator_id=group.creator_id,
                member_count=len(m_users),
                members=[
                    GroupMemberSchema(
                        id=u.id,
                        name=u.name,
                        leetcode_username=u.leetcode_username,
                        avatar_url=u.avatar_url,
                    )
                    for u in m_users
                ],
            )
        )

    return GroupListResponse(groups=group_responses)


@app.delete("/api/groups/{group_id}/members/{user_id}")
def remove_group_member(group_id: int, user_id: int, requester_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.creator_id != requester_id and user_id != requester_id:
        raise HTTPException(status_code=403, detail="Only the group owner or member themselves can remove from group.")

    mem = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if mem:
        db.delete(mem)
        db.commit()

    return {"status": "removed", "group_id": group_id, "user_id": user_id}


@app.get("/api/groups/{group_id}/leaderboard", response_model=LeaderboardResponse)
def get_group_leaderboard(
    group_id: int,
    user_id: Optional[int] = Query(None),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    users = (
        db.query(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return _compute_leaderboard(db, users, requester_id=user_id, sort_by=sort_by, limit=limit)


@app.post("/api/kudos/{to_user_id}")
def toggle_kudos(to_user_id: int, payload: KudosToggleRequest, db: Session = Depends(get_db)):
    from_id = payload.from_user_id
    if from_id == to_user_id:
        raise HTTPException(status_code=400, detail="You cannot give kudos to yourself.")

    to_user = db.query(User).filter(User.id == to_user_id).first()
    if not to_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    existing = (
        db.query(Kudos)
        .filter(Kudos.from_user_id == from_id, Kudos.to_user_id == to_user_id)
        .first()
    )
    cutoff_today = get_ist_today_start()

    if existing:
        if existing.created_at >= cutoff_today:
            db.delete(existing)
            db.commit()
            status = "removed"
        else:
            existing.created_at = datetime.now()
            db.commit()
            status = "renewed"
    else:
        k = Kudos(from_user_id=from_id, to_user_id=to_user_id)
        db.add(k)
        db.commit()
        status = "added"

    active_count = (
        db.query(Kudos)
        .filter(Kudos.to_user_id == to_user_id, Kudos.created_at >= cutoff_today)
        .count()
    )
    has_active = status in ["added", "renewed"]
    return {
        "status": status,
        "to_user_id": to_user_id,
        "kudos_count": active_count,
        "has_kudosed": has_active,
    }


def _time_ago(dt: datetime) -> str:
    now = datetime.now()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    return f"{months}mo ago"


@app.get("/api/users/{user_id}/recent-solves", response_model=List[RecentSolveSchema])
async def get_user_recent_solves(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    solves = (
        db.query(Solve)
        .filter(Solve.user_id == user_id)
        .order_by(Solve.solved_at.desc())
        .limit(limit)
        .all()
    )

    if not solves:
        # Fallback: poll LeetCode on demand if solves ledger is empty
        await poll_user(db, user)
        solves = (
            db.query(Solve)
            .filter(Solve.user_id == user_id)
            .order_by(Solve.solved_at.desc())
            .limit(limit)
            .all()
        )

    return [
        RecentSolveSchema(
            title_slug=s.title_slug,
            title=s.title or s.title_slug.replace("-", " ").title(),
            solved_at=s.solved_at,
            relative_time=_time_ago(s.solved_at),
            leetcode_url=f"https://leetcode.com/problems/{s.title_slug}",
        )
        for s in solves
    ]


@app.get("/api/feed/recent-solves", response_model=List[ActivityFeedItemSchema])
async def get_global_recent_solves(limit: int = 15, db: Session = Depends(get_db)):
    """Returns the latest solved questions from all users across the platform in chronological order."""
    solves = (
        db.query(Solve, User)
        .join(User, Solve.user_id == User.id)
        .order_by(Solve.solved_at.desc())
        .limit(limit)
        .all()
    )

    feed = []
    for solve, user in solves:
        title = solve.title or solve.title_slug.replace("-", " ").title()
        feed.append(
            ActivityFeedItemSchema(
                user_id=user.id,
                user_name=user.name,
                user_handle=user.leetcode_username,
                title=title,
                title_slug=solve.title_slug,
                solved_at=solve.solved_at,
                relative_time=_time_ago(solve.solved_at),
                leetcode_url=f"https://leetcode.com/problems/{solve.title_slug}",
            )
        )
    return feed


@app.post("/api/admin/poll-now")
async def poll_now():
    """Manually trigger a poll of all users."""
    results = await poll_all_users()
    return {"polled": results}


@app.post("/api/admin/reset-db", dependencies=[Depends(verify_admin_secret)])
def reset_db(db: Session = Depends(get_db)):
    """Clears all database records for fresh user registrations."""
    db.query(Solve).delete()
    db.query(DailyActivity).delete()
    db.query(GroupMember).delete()
    db.query(Group).delete()
    db.query(User).delete()
    db.commit()
    return {"status": "database_reset_success"}


@app.get("/api/admin/debug-users", dependencies=[Depends(verify_admin_secret)])
def debug_users(db: Session = Depends(get_db)):
    """Inspect all registered users in the database and their password auth status."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "leetcode_username": u.leetcode_username,
            "email": u.email,
            "has_password": bool(u.password_hash),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@app.get("/api/admin/init-user-dates", dependencies=[Depends(verify_admin_secret)])
def init_user_dates(db: Session = Depends(get_db)):
    """Backfills created_at timestamp for existing users."""
    users = db.query(User).all()
    count = 0
    now = datetime.now()
    for u in users:
        if not u.created_at:
            u.created_at = now
            count += 1
    db.commit()
    return {"status": "initialized", "updated_count": count}


@app.delete("/api/admin/users/{user_id}", dependencies=[Depends(verify_admin_secret)])
def delete_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(Solve).filter(Solve.user_id == user_id).delete()
    db.query(DailyActivity).filter(DailyActivity.user_id == user_id).delete()
    db.query(GroupMember).filter(GroupMember.user_id == user_id).delete()

    deleted_username = user.leetcode_username
    db.delete(user)
    db.commit()
    return {"status": "deleted", "user_id": user_id, "username": deleted_username}


# ==========================================================================
# 🚀 EXTENSION OVER-THE-AIR (OTA) AUTO-UPDATE ENDPOINTS
# ==========================================================================
@app.get("/api/extension/updates.xml")
def get_extension_updates_xml():
    """Serves official Chrome Omaha XML manifest for background auto-updates."""
    xml_content = """<?xml version='1.0' encoding='UTF-8'?>
<gupdate xmlns='http://www.google.com/service/update2/crx' protocol='2.0'>
  <app appid='leetstreak@example.com'>
    <updatecheck codebase='https://leetcode-leetstreak.onrender.com/downloads/leetstreak.crx' version='1.0.0' />
  </app>
</gupdate>"""
    return Response(content=xml_content, media_type="application/xml")


@app.get("/api/extension/version")
def get_extension_version():
    """Serves latest extension version info for in-app update notification banner."""
    return {
        "latest_version": "1.0.0",
        "min_supported_version": "1.0.0",
        "release_notes": "Added Buy Me a Coffee feature, Sunday 12am reset, and full Firefox support!",
        "download_url": "https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/leetstreak.zip",
        "crx_url": "https://leetcode-leetstreak.onrender.com/downloads/leetstreak.crx"
    }


@app.get("/downloads/leetstreak.zip")
def download_extension_zip():
    """Serves downloadable leetstreak.zip file."""
    zip_path = os.path.join(os.path.dirname(__file__), "..", "..", "leetstreak.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="leetstreak.zip", media_type="application/zip")
    return {"error": "Extension package file not found"}


# ==========================================================================
# 🌐 DYNAMIC BACKEND-DRIVEN OTA APP CONFIG & MENU ENDPOINT
# ==========================================================================
@app.get("/api/config/app", response_model=AppConfigResponse)
def get_app_config():
    """Serves dynamic over-the-air app configuration, feature flags, announcements, and dynamic menus."""
    return AppConfigResponse(
        version="1.0.0",
        maintenance_mode=False,
        announcement=None,
        menu_items=[
            DynamicMenuItem(id="dashboard", label="Dashboard", icon="📊", type="tab", enabled=True),
            DynamicMenuItem(id="groups", label="Groups", icon="👥", type="tab", enabled=True),
            DynamicMenuItem(id="coffee", label="Buy Me a Coffee", icon="☕", type="modal", enabled=True),
        ]
    )


