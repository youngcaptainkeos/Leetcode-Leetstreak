import logging
import secrets
import string
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS
from .database import Base, engine, get_db
from .models import User, DailyActivity, Group, GroupMember, Solve
from .auth import hash_password, verify_password
from .email_service import send_otp_email
from .schemas import (
    RegisterRequest, RegisterResponse, DashboardResponse, DayCount,
    LeaderboardResponse, LeaderboardEntry, GroupCreateRequest, GroupJoinRequest,
    GroupResponse, GroupListResponse, GroupMemberSchema, RecentSolveSchema,
    LoginRequest, ForgotPasswordInitiateRequest, ForgotPasswordVerifyRequest,
)
from .streak import current_streak
from .scheduler import start_scheduler, poll_all_users, poll_user
from .leetcode_client import fetch_leetcode_user_data, LeetCodeError

from sqlalchemy import text

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

# Safe auto-migration for existing PostgreSQL/SQLite tables
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(120);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(200);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_otp VARCHAR(6);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;"))
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

    canonical_username = data.get("username", payload.leetcode_username)
    existing = db.query(User).filter(User.leetcode_username == canonical_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="That LeetCode username is already registered. Please log in instead.")

    user = User(
        name=payload.name,
        leetcode_username=canonical_username,
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        avatar_url=data.get("avatar_url"),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="That LeetCode username or email is already registered.")
    db.refresh(user)

    # Ingest full history
    await poll_user(db, user)

    return RegisterResponse(
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        avatar_url=user.avatar_url,
    )


@app.post("/api/users/login", response_model=RegisterResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    query_str = payload.leetcode_username.strip()
    user = (
        db.query(User)
        .filter((User.leetcode_username == query_str) | (User.email == query_str.lower()))
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Invalid username/email or password.")

    return RegisterResponse(
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        avatar_url=user.avatar_url,
    )


@app.post("/api/users/forgot-password/initiate")
async def initiate_forgot_password(payload: ForgotPasswordInitiateRequest, db: Session = Depends(get_db)):
    query_str = payload.email_or_username.strip()
    user = (
        db.query(User)
        .filter((User.leetcode_username == query_str) | (User.email == query_str.lower()))
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
    query_str = payload.email_or_username.strip()
    user = (
        db.query(User)
        .filter((User.leetcode_username == query_str) | (User.email == query_str.lower()))
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


def _active_dates(db: Session, user_id: int) -> set[date]:
    rows = (
        db.query(DailyActivity.date)
        .filter(DailyActivity.user_id == user_id, DailyActivity.problems_solved > 0)
        .all()
    )
    return {r[0] for r in rows}


@app.get("/api/users/{user_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    active_dates = _active_dates(db, user_id)
    streak = current_streak(active_dates, today)

    def total_since(days: int) -> int:
        start = today - timedelta(days=days - 1)
        rows = (
            db.query(DailyActivity)
            .filter(DailyActivity.user_id == user_id, DailyActivity.date >= start)
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
        weekly_total=total_since(7),
        monthly_total=total_since(30),
        last_7_days=last_7,
    )


def _compute_leaderboard(db: Session, users: List[User]) -> LeaderboardResponse:
    today = date.today()
    week_start = today - timedelta(days=6)

    raw = []
    for user in users:
        active_dates = _active_dates(db, user.id)
        streak = current_streak(active_dates, today)
        week_rows = (
            db.query(DailyActivity)
            .filter(DailyActivity.user_id == user.id, DailyActivity.date >= week_start)
            .all()
        )
        weekly_total = sum(r.problems_solved for r in week_rows)
        active_days_this_week = sum(1 for r in week_rows if r.problems_solved > 0)
        consistency = (active_days_this_week / 7) * 100
        is_active_today = today in active_dates
        points = ((user.easy_count or 0) * 1) + ((user.medium_count or 0) * 3) + ((user.hard_count or 0) * 6)
        raw.append({
            "user": user,
            "weekly_total": weekly_total,
            "streak": streak,
            "consistency": consistency,
            "points": points,
            "is_active_today": is_active_today,
        })

    max_weekly = max((r["weekly_total"] for r in raw), default=0) or 1
    for r in raw:
        normalized_volume = (r["weekly_total"] / max_weekly) * 100
        r["combined"] = round(0.6 * r["consistency"] + 0.4 * normalized_volume, 1)

    raw.sort(key=lambda r: (r["points"], r["combined"]), reverse=True)

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
        )
        for i, r in enumerate(raw)
    ]

    return LeaderboardResponse(week_start=week_start, week_end=today, entries=entries)


@app.get("/api/leaderboard", response_model=LeaderboardResponse)
def get_global_leaderboard(user_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if user_id:
        # Find all group IDs the user belongs to
        user_group_ids = [
            m[0] for m in db.query(GroupMember.group_id).filter(GroupMember.user_id == user_id).all()
        ]
        if user_group_ids:
            # Find all member user IDs across all those groups
            co_member_ids = {
                m[0] for m in db.query(GroupMember.user_id).filter(GroupMember.group_id.in_(user_group_ids)).all()
            }
            co_member_ids.add(user_id)
            users = db.query(User).filter(User.id.in_(co_member_ids)).all()
        else:
            # User has no groups yet, show only themselves
            users = db.query(User).filter(User.id == user_id).all()
    else:
        users = db.query(User).all()

    return _compute_leaderboard(db, users)


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
def get_group_leaderboard(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    users = (
        db.query(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return _compute_leaderboard(db, users)


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


@app.post("/api/admin/poll-now")
async def poll_now():
    """Manually trigger a poll of all users."""
    results = await poll_all_users()
    return {"polled": results}

