import os
import logging
import asyncio
import secrets

logger = logging.getLogger("codestreak.main")
import string
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Set

from fastapi import FastAPI, HTTPException, Depends, Query, Header, BackgroundTasks, Request
from fastapi.responses import Response, FileResponse, HTMLResponse
from .legal_pages import PRIVACY_HTML, TERMS_HTML
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS, ADMIN_SECRET
from .database import Base, engine, get_db, SessionLocal
from .models import AccountCredit, AccountProgress, AdminOperation, User, PlatformActivity, DailyActivity, Group, GroupMember, Solve, Kudos, DailyChallenge
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from .email_service import send_otp_email, send_update_notification_email
from .schemas import (
    RegisterRequest, RegisterResponse, DashboardResponse, DayCount,
    LeaderboardResponse, LeaderboardEntry, GroupCreateRequest, GroupJoinRequest,
    GroupResponse, GroupListResponse, GroupMemberSchema, RecentSolveSchema, PointBreakdownSchema,
    LoginRequest, ForgotPasswordInitiateRequest, ForgotPasswordVerifyRequest,
    KudosToggleRequest, KudosAllRequest, UpdateUsernameRequest, UpdateSettingsRequest, ActivityFeedItemSchema,
    DynamicMenuItem, AppConfigResponse, DeleteAccountRequest, SyncRequest, UpdateCodeforcesRequest, GroupTransferRequest, ReleaseBroadcastRequest, ChangePasswordRequest,
)
from .streak import current_streak
from .timekeeping import IST, ist_today, week_start as product_week_start, month_start as product_month_start, period_bounds
from .scheduler import start_scheduler, poll_all_users, poll_user
from .leetcode_client import fetch_leetcode_user_data, fetch_today_daily_challenge_slug, fetch_problem_info, LeetCodeError
from .point_calculator import recalculate_user_points
from .reconciliation import current_account, stored_breakdown
from .locked_scoring import credit_total
from .platforms import activity_counts, daily_counts, streak_dates, solve_url
from .codeforces_client import fetch_profile, CodeforcesError
from .codeforces_sync import background_codeforces_sync, user_sync_lock
from .security import current_user, require_self, member_group, owned_group
from .releases import RELEASE_NOTICES
from .migrations import run_migrations
from .recovery import consume_limit, recovery_account, otp_verifier, clear_reset, utcnow
from .tracking import clear_tracking, capture_score_baseline
from .progress import router as progress_router
from .sync_jobs import router as sync_jobs_router
from .reviewer import provision_reviewer, require_mutable_identity, require_visible_profile, require_social_participant, require_group_scope


def verify_admin_secret(x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret")):
    if len(ADMIN_SECRET.encode("utf-8")) < 32 or not x_admin_secret or not secrets.compare_digest(x_admin_secret.encode("utf-8"), ADMIN_SECRET.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Secret Header")
    return True

logging.basicConfig(level=logging.INFO)
# Queue checks are normally idle; retain their warnings/errors without printing
# two scheduler messages every five seconds. Actual poll start/end is logged above.
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

app = FastAPI(title="LeetStreak API")
app.include_router(progress_router)
app.include_router(sync_jobs_router)
app.state.schema_ready = False

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
    app.state.schema_ready = False
    # Exceptions must propagate: never serve a partially migrated schema.
    await asyncio.to_thread(run_migrations, engine)
    await asyncio.to_thread(provision_reviewer, engine)
    from .sync_jobs import resume_sync_jobs
    resume_sync_jobs()
    _scheduler = start_scheduler()
    app.state.schema_ready = True


@app.on_event("shutdown")
async def on_shutdown():
    global _scheduler
    app.state.schema_ready = False
    from .sync_jobs import stop_sync_jobs
    await stop_sync_jobs()
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


@app.get("/api/ready")
def readiness():
    if not app.state.schema_ready:
        raise HTTPException(status_code=503, detail="Service is not ready")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        # Do not return connection strings, credentials or driver diagnostics.
        raise HTTPException(status_code=503, detail="Database is unavailable") from None
    return {"status": "ready"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return HTMLResponse(content=PRIVACY_HTML)


@app.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    return HTMLResponse(content=TERMS_HTML)


def _generate_group_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "STREAK-" + "".join(secrets.choice(chars) for _ in range(length))


@app.post("/api/users/register", response_model=RegisterResponse)
async def register_user(payload: RegisterRequest, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    consume_limit(db, "register-peer", request.client.host if request.client else "unknown", 20, 3600)
    consume_limit(db, "register-address", payload.email, 5, 3600)
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

    codeforces_handle = None
    if payload.codeforces_username and payload.codeforces_username.strip():
        db.commit()
        try:
            profile = await fetch_profile(payload.codeforces_username)
        except CodeforcesError as error:
            raise HTTPException(status_code=400, detail=f"Codeforces: {error} You can leave that optional field blank and add it later.")
        codeforces_handle = profile["handle"]
        if db.query(User.id).filter(func.lower(User.codeforces_username) == codeforces_handle.lower()).first():
            raise HTTPException(status_code=409, detail="That Codeforces handle is already connected. Leave it blank to continue without Codeforces.")

    canonical_username = data.get("username", payload.leetcode_username)

    user = User(
        name=payload.name,
        leetcode_username=canonical_username,
        codeforces_username=codeforces_handle,
        codeforces_linked_at=datetime.now(timezone.utc).replace(tzinfo=None) if codeforces_handle else None,
        email=clean_email,
        password_hash=hash_password(payload.password),
        avatar_url=data.get("avatar_url"),
        global_leaderboard_enabled=payload.show_global_leaderboard if payload.show_global_leaderboard is not None else payload.global_leaderboard_enabled,
        show_global_leaderboard=payload.show_global_leaderboard if payload.show_global_leaderboard is not None else payload.global_leaderboard_enabled,
        created_at=utcnow(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email or Codeforces handle is already registered.")
    db.refresh(user)

    # Public profile/recent AC sync remains partial history, not first-solve proof.
    await poll_user(db, user, sync_codeforces=False)
    if codeforces_handle:
        background_tasks.add_task(background_codeforces_sync, user.id)

    token = create_access_token(user.id, user.session_version)
    return RegisterResponse(
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        codeforces_username=user.codeforces_username,
        avatar_url=user.avatar_url,
        access_token=token,
        token_type="bearer",
        created_at=user.created_at,
        global_leaderboard_enabled=user.show_global_leaderboard,
        show_global_leaderboard=user.show_global_leaderboard,
    )


@app.post("/api/users/login", response_model=RegisterResponse)
def login_user(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    query_str = payload.leetcode_username.strip().lower()
    consume_limit(db, "login-peer", request.client.host if request.client else "unknown", 60, 900)
    consume_limit(db, "login-account", query_str, 10, 900)
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

    token = create_access_token(matched_user.id, matched_user.session_version)
    return RegisterResponse(
        id=matched_user.id,
        name=matched_user.name,
        leetcode_username=matched_user.leetcode_username,
        codeforces_username=matched_user.codeforces_username,
        avatar_url=matched_user.avatar_url,
        access_token=token,
        token_type="bearer",
        created_at=matched_user.created_at,
        global_leaderboard_enabled=matched_user.show_global_leaderboard,
        show_global_leaderboard=matched_user.show_global_leaderboard,
    )


async def deliver_reset(user_id: int, request_id: str, address: str, name: str, code: str):
    result = await send_otp_email(address, name, code)
    if not result:
        with SessionLocal() as db:
            user = db.query(User).filter_by(id=user_id).with_for_update().first()
            if user and user.otp_request_id == request_id:
                clear_reset(user)
                db.commit()
        logger.warning("Password reset delivery not accepted; code invalidated.")


@app.post("/api/users/forgot-password/initiate")
def initiate_forgot_password(payload: ForgotPasswordInitiateRequest, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    identifier = payload.email_or_username.strip().lower()
    consume_limit(db, "reset-request-peer", request.client.host if request.client else "unknown", 20, 900)
    consume_limit(db, "reset-request-account", identifier, 3, 3600)
    message = {"status": "request_received", "message": "If a unique matching account exists, a reset code will be sent to its registered email. If a username is shared, use your email address."}
    user = recovery_account(db, identifier)
    if not user or user.is_reviewer:
        return message
    db.refresh(user, with_for_update=True)
    now = utcnow()
    if user.otp_last_requested_at and now - user.otp_last_requested_at < timedelta(seconds=60):
        return message
    clear_reset(user)
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    user.otp_request_id = secrets.token_hex(24)
    user.reset_otp_hash = otp_verifier(user.id, user.otp_request_id, code)
    user.otp_expires_at = now + timedelta(minutes=15)
    user.otp_last_requested_at = now
    db.commit()
    background_tasks.add_task(deliver_reset, user.id, user.otp_request_id, user.email, user.name, code)
    return message


@app.post("/api/users/forgot-password/verify")
def verify_forgot_password(payload: ForgotPasswordVerifyRequest, request: Request, db: Session = Depends(get_db)):
    identifier = payload.email_or_username.strip().lower()
    consume_limit(db, "reset-verify-peer", request.client.host if request.client else "unknown", 100, 900)
    consume_limit(db, "reset-verify-account", identifier, 10, 900)
    user = recovery_account(db, identifier)
    denied = HTTPException(400, "Invalid or expired reset code. Request a new code if needed.")
    if not user or user.is_reviewer:
        raise denied
    db.refresh(user, with_for_update=True)
    if not user.reset_otp_hash or not user.otp_request_id or not user.otp_expires_at or user.otp_expires_at <= utcnow() or user.otp_attempts >= 5:
        clear_reset(user)
        db.commit()
        raise denied
    user.otp_attempts += 1
    expected = otp_verifier(user.id, user.otp_request_id, payload.otp)
    if not secrets.compare_digest(user.reset_otp_hash, expected):
        if user.otp_attempts >= 5:
            clear_reset(user)
        db.commit()
        raise denied
    user.password_hash = hash_password(payload.new_password)
    user.session_version += 1
    clear_reset(user)
    db.commit()
    return {"status": "password_reset_success"}


@app.post("/api/users/{user_id}/change-password")
def change_password(user_id: int, payload: ChangePasswordRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    require_mutable_identity(actor)
    consume_limit(db, "change-password", str(actor.id), 5, 900)
    db.refresh(actor, with_for_update=True)
    if not verify_password(payload.current_password, actor.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    actor.password_hash = hash_password(payload.new_password)
    actor.session_version += 1
    clear_reset(actor)
    db.commit()
    return {"status": "password_changed", "access_token": create_access_token(actor.id, actor.session_version)}


@app.post("/api/users/{user_id}/revoke-sessions")
def revoke_sessions(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    db.refresh(actor, with_for_update=True)
    actor.session_version += 1
    db.commit()
    return {"status": "sessions_revoked"}


@app.post("/api/users/{user_id}/sync")
async def sync_user(user_id: int, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db), actor: User = Depends(current_user)):
    from .sync_jobs import legacy_sync
    require_self(actor, user_id)
    return await legacy_sync(user_id, background_tasks, db, actor)


@app.put("/api/users/{user_id}/leetcode-username")
async def update_leetcode_username(user_id: int, payload: UpdateUsernameRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    require_mutable_identity(actor)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_username = payload.leetcode_username.strip()
    if not new_username:
        raise HTTPException(status_code=400, detail="LeetCode username cannot be empty.")

    expected = (user.leetcode_username, user.leetcode_account_version)
    db.commit()
    try:
        data = await fetch_leetcode_user_data(new_username)
    except LeetCodeError as err:
        raise HTTPException(status_code=400, detail=str(err))
    canonical = data.get("username")
    if not isinstance(canonical, str) or canonical.casefold() != new_username.casefold():
        raise HTTPException(status_code=400, detail="The provider did not confirm that LeetCode username.")

    db.refresh(user, with_for_update=True)
    if (user.leetcode_username, user.leetcode_account_version) != expected:
        db.rollback()
        raise HTTPException(status_code=409, detail="Your coding account changed. Refresh before trying again.")
    if user.leetcode_username.casefold() != canonical.casefold():
        capture_score_baseline(db, user_id)
        capture_score_baseline(db, user_id,
            snapshot_key=f"replacement:{user_id}:leetcode:{user.leetcode_account_version}", reason="account-replacement")
        clear_tracking(db, user_id, "leetcode")
        db.query(Solve).filter_by(user_id=user_id, platform="leetcode").delete(synchronize_session=False)
        db.query(DailyActivity).filter_by(user_id=user_id).delete(synchronize_session=False)
        user.leetcode_account_version += 1
        user.leetcode_last_sync = None
        user.leetcode_history_state = "partial"
        user.leetcode_history_gap = True
        counts = data.get("difficulty_counts") or {}
        user.easy_count = counts.get("Easy", 0)
        user.medium_count = counts.get("Medium", 0)
        user.hard_count = counts.get("Hard", 0)
        user.official_streak = data.get("official_streak", 0)
    user.leetcode_username = canonical
    user.avatar_url = data.get("avatar_url")
    recalculate_user_points(user, db)
    db.commit()

    await poll_user(db, user)

    return {
        "status": "username_updated",
        "user_id": user_id,
        "leetcode_username": user.leetcode_username,
        "avatar_url": user.avatar_url,
    }


@app.put("/api/users/{user_id}/codeforces-username")
async def update_codeforces_username(user_id: int, payload: UpdateCodeforcesRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    require_mutable_identity(actor)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_sync_lock(user_id).locked():
        raise HTTPException(status_code=409, detail="Your Codeforces history is syncing. Please wait before changing the handle.")
    db.commit()
    try:
        profile = await fetch_profile(payload.codeforces_username)
    except CodeforcesError as error:
        raise HTTPException(status_code=400, detail=str(error))
    handle = profile["handle"]
    owner = db.query(User.id).filter(func.lower(User.codeforces_username) == handle.lower(), User.id != user_id).first()
    if owner:
        raise HTTPException(status_code=409, detail="That Codeforces handle is already connected to another account.")
    async with user_sync_lock(user_id):
        db.refresh(user, with_for_update=True)
        if not user.codeforces_username or user.codeforces_username.lower() != handle.lower():
            capture_score_baseline(db, user_id)
            capture_score_baseline(db, user_id,
                snapshot_key=f"replacement:{user_id}:codeforces:{user.codeforces_account_version}", reason="account-replacement")
            user.codeforces_account_version += 1
            user.codeforces_linked_at = utcnow()
            clear_tracking(db, user_id, "codeforces")
            db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").delete()
            db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id, PlatformActivity.platform == "codeforces").delete()
            user.codeforces_last_sync = None
            user.codeforces_last_full_sync = None
        user.codeforces_username = handle
        user.codeforces_linked_at = user.codeforces_linked_at or datetime.now(timezone.utc).replace(tzinfo=None)
        user.codeforces_sync_error = None
        recalculate_user_points(user, db)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="That Codeforces handle was just connected to another account.")
    background_tasks.add_task(background_codeforces_sync, user_id)
    return {"status": "syncing", "codeforces_username": handle}


@app.put("/api/users/{user_id}/settings")
def update_user_settings(user_id: int, payload: UpdateSettingsRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.show_global_leaderboard = payload.show_global_leaderboard if payload.show_global_leaderboard is not None else payload.global_leaderboard_enabled
    user.global_leaderboard_enabled = user.show_global_leaderboard
    db.commit()
    db.refresh(user)

    return {
        "status": "settings_updated",
        "user_id": user_id,
        "global_leaderboard_enabled": user.show_global_leaderboard,
        "show_global_leaderboard": user.show_global_leaderboard,
    }


@app.post("/api/users/{user_id}/delete-account")
def delete_user_account(user_id: int, payload: DeleteAccountRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    require_mutable_identity(actor)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password. Account deletion failed.")

    if db.query(Group.id).filter(Group.creator_id == actor.id).first():
        raise HTTPException(409, "Transfer ownership or delete your groups before deleting your account.")

    from .models import UserSyncJob
    db.query(UserSyncJob).filter_by(user_id=user_id).delete()
    clear_tracking(db, user_id)
    db.query(AccountProgress).filter_by(user_id=user_id).delete()
    db.query(GroupMember).filter(GroupMember.user_id == user_id).delete()
    db.query(DailyActivity).filter(DailyActivity.user_id == user_id).delete()
    db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id).delete()
    db.query(Solve).filter(Solve.user_id == user_id).delete()
    db.query(Kudos).filter((Kudos.from_user_id == user_id) | (Kudos.to_user_id == user_id)).delete()
    db.query(Group).filter(Group.creator_id == user_id).update({Group.creator_id: None})

    db.delete(user)
    db.commit()

    return {"status": "account_deleted", "message": "Account deleted successfully"}


def _active_dates(db: Session, user_id: int) -> set[date]:
    return streak_dates(db, [user_id])[user_id]


def get_ist_today() -> date:
    """Returns today's date in Indian Standard Time (IST, UTC+5:30)."""
    return ist_today()


def get_current_week_start(today: date) -> date:
    """Returns Sunday 00:00:00 (start of current week). Resets weekly counter every Sunday 12:00 AM."""
    return product_week_start(today)


def get_current_month_start(today: date) -> date:
    """Returns 1st of the current calendar month 00:00:00. Resets monthly counter on the 1st of every month."""
    return product_month_start(today)


def get_ist_today_start() -> datetime:
    """Returns midnight (00:00:00) of current calendar day in Indian Standard Time (IST, UTC+5:30) converted to naive UTC for DB comparison."""
    start, _ = period_bounds("today", get_ist_today())
    return start


@app.get("/api/users/{user_id}/dashboard", response_model=DashboardResponse, response_model_exclude_none=True)
def get_dashboard(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    require_visible_profile(actor, user)

    today = get_ist_today()
    week_start = get_current_week_start(today)
    month_start = get_current_month_start(today)

    active_dates = _active_dates(db, user_id)
    streak = current_streak(active_dates, today)

    combined = daily_counts(db, [user_id])[user_id]
    def total_since_date(start_date: date) -> int:
        return sum(count for day, count in combined.items() if day >= start_date)
    activity = activity_counts(db, [user_id], today=today)[user_id]
    last_7 = [DayCount(date=today - timedelta(days=i), problems_solved=activity.get(today - timedelta(days=i), 0)) for i in range(6, -1, -1)]
    cf_count, cf_points = db.query(func.count(Solve.id), func.coalesce(func.sum(Solve.points_earned), 0)).filter(Solve.user_id == user_id, Solve.platform == "codeforces").one()
    cf_balance = db.query(AccountCredit).filter_by(user_id=user_id, platform="codeforces",
        account_version=user.codeforces_account_version, kind="locked_balance").first()
    if cf_balance and user.codeforces_username:
        cf_points = credit_total(cf_balance)

    estimate = db.query(AccountCredit).filter_by(user_id=user.id, platform="leetcode", account_version=user.leetcode_account_version, kind="historical_base").first()
    needs_review = db.query(Solve.id).filter(Solve.user_id == user.id, Solve.score_components_state.in_(["legacy", "legacy_protected", "metadata_missing", "history_review"])).first() is not None
    return DashboardResponse(
        history_incomplete=user.leetcode_history_gap or any(not row.first_solve_verified for row in db.query(Solve).filter_by(user_id=user.id).all()),
        historical_base_points=float(estimate.points) if estimate else 0,
        score_needs_review=needs_review,
        codeforces_last_sync=user.codeforces_last_sync.replace(tzinfo=timezone.utc) if user.codeforces_last_sync else None, codeforces_sync_error=user.codeforces_sync_error if actor.id == user_id else None,
        codeforces_count=cf_count, codeforces_points=round(float(cf_points), 4), leetcode_points=round((user.points or 0) - float(cf_points), 4), points=user.points or 0,
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        codeforces_username=user.codeforces_username,
        avatar_url=user.avatar_url,
        easy_count=user.easy_count or 0,
        medium_count=user.medium_count or 0,
        hard_count=user.hard_count or 0,
        current_streak=streak,
        today_count=combined.get(today, 0),
        weekly_total=total_since_date(week_start),
        monthly_total=total_since_date(month_start),
        created_at=user.created_at,
        last_7_days=last_7,
        global_leaderboard_enabled=user.show_global_leaderboard if actor.id == user_id else None,
        show_global_leaderboard=user.show_global_leaderboard if actor.id == user_id else None,
    )


def _compute_leaderboard(
    db: Session,
    users: List[User],
    requester_id: Optional[int] = None,
    sort_by: str = "points",
    limit: Optional[int] = None,
) -> LeaderboardResponse:
    users = [user for user in users if not user.is_reviewer]
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

    combined = daily_counts(db, user_ids)
    display_dates = streak_dates(db, user_ids, today=today, verified_counts=combined)
    cf_stats = {row[0]: (row[1], float(row[2])) for row in db.query(Solve.user_id, func.count(Solve.id), func.coalesce(func.sum(Solve.points_earned), 0)).filter(Solve.user_id.in_(user_ids), Solve.platform == "codeforces").group_by(Solve.user_id).all()}
    by_id = {user.id: user for user in users}
    for balance in db.query(AccountCredit).filter(AccountCredit.user_id.in_(user_ids),
            AccountCredit.platform == "codeforces", AccountCredit.kind == "locked_balance").all():
        owner = by_id[balance.user_id]
        if owner.codeforces_username and balance.account_version == owner.codeforces_account_version:
            cf_stats[owner.id] = (cf_stats.get(owner.id, (0, 0))[0], float(credit_total(balance)))

    raw = []
    for user in users:
        dates = combined[user.id]
        active_dates = display_dates[user.id]
        streak = current_streak(active_dates, today)
        week_rows = {day: count for day, count in dates.items() if week_start <= day <= today}
        weekly_total = sum(week_rows.values())
        active_days_this_week = len(week_rows)
        consistency = (active_days_this_week / days_in_week_so_far) * 100
        is_active_today = today in active_dates
        points = float(user.points or 0.0)
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
            codeforces_username=r["user"].codeforces_username,
            codeforces_count=cf_stats.get(r["user"].id, (0, 0))[0],
            codeforces_points=round(cf_stats.get(r["user"].id, (0, 0))[1], 4),
            leetcode_points=round((r["user"].points or 0) - cf_stats.get(r["user"].id, (0, 0))[1], 4),
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

    total_users = len(entries)

    # Top Limit + User Rank Pinning (includes 1 rank above and 1 rank below when requester is outside Top N)
    if limit is not None and len(entries) > limit:
        top_entries = entries[:limit]
        if requester_id is not None:
            user_in_top = any(e.id == requester_id for e in top_entries)
            if not user_in_top:
                req_idx = next((idx for idx, e in enumerate(entries) if e.id == requester_id), None)
                if req_idx is not None:
                    pinned_indices = set()
                    if req_idx > 0 and req_idx - 1 >= limit:
                        pinned_indices.add(req_idx - 1)  # 1 user above
                    pinned_indices.add(req_idx)          # Requester themselves
                    if req_idx + 1 < len(entries):
                        pinned_indices.add(req_idx + 1)  # 1 user below

                    for p_i in sorted(pinned_indices):
                        top_entries.append(entries[p_i])
        entries = top_entries

    return LeaderboardResponse(week_start=week_start, week_end=today, total_users=total_users, entries=entries)


@app.get("/api/leaderboard", response_model=LeaderboardResponse)
def get_global_leaderboard(
    user_id: Optional[int] = Query(None),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user_id = actor.id
    # Every account participates; the preference controls only the viewer's UI.
    users = db.query(User).filter(User.is_reviewer.is_(False)).all()
    return _compute_leaderboard(db, users, requester_id=user_id, sort_by=sort_by, limit=limit)


@app.get("/api/friends/leaderboard", response_model=LeaderboardResponse)
def get_friends_leaderboard(
    user_id: int = Query(...),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user_id = actor.id
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
def create_group(payload: GroupCreateRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, payload.user_id)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = _generate_group_code()
    group = Group(name=payload.name, code=code, creator_id=user.id)
    db.add(group)
    try:
        db.flush()
        db.add(GroupMember(group_id=group.id, user_id=actor.id))
        db.commit()
        db.refresh(group)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Could not create the group. Please retry.")

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
                codeforces_username=user.codeforces_username,
                avatar_url=user.avatar_url,
            )
        ],
    )


@app.post("/api/groups/join", response_model=GroupResponse)
def join_group(payload: GroupJoinRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, payload.user_id)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code_clean = payload.code.strip().upper()
    group = db.query(Group).filter(Group.code == code_clean).first()
    if not group:
        raise HTTPException(status_code=404, detail="Invalid group code. Please check the code and try again.")
    require_group_scope(db, actor, group)

    existing_mem = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
        .first()
    )
    if not existing_mem:
        db.add(GroupMember(group_id=group.id, user_id=user.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if not db.query(GroupMember.id).filter_by(group_id=group.id, user_id=actor.id).first():
                raise HTTPException(409, "Could not join the group. Please retry.")

    members = (
        db.query(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group.id)
        .filter(or_(User.is_reviewer.is_(False), User.id == actor.id))
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
                codeforces_username=m.codeforces_username,
                avatar_url=m.avatar_url,
            )
            for m in members
        ],
    )


@app.get("/api/groups/my-groups/{user_id}", response_model=GroupListResponse)
def get_my_groups(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    groups = (
        db.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.user_id == user_id)
        .all()
    )
    if not groups:
        return GroupListResponse(groups=[])

    group_ids = [g.id for g in groups]
    # Fetch all members of these groups in a single batch query
    all_memberships = (
        db.query(GroupMember.group_id, User)
        .join(User, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id.in_(group_ids))
        .filter(or_(User.is_reviewer.is_(False), User.id == actor.id))
        .all()
    )

    group_members_map = defaultdict(list)
    for g_id, user_obj in all_memberships:
        group_members_map[g_id].append(
            GroupMemberSchema(
                id=user_obj.id,
                name=user_obj.name,
                leetcode_username=user_obj.leetcode_username,
                codeforces_username=user_obj.codeforces_username,
                avatar_url=user_obj.avatar_url,
            )
        )

    group_responses = [
        GroupResponse(
            id=g.id,
            name=g.name,
            code=g.code,
            creator_id=g.creator_id,
            member_count=len(group_members_map[g.id]),
            members=group_members_map[g.id],
        )
        for g in groups
    ]

    return GroupListResponse(groups=group_responses)


@app.delete("/api/groups/{group_id}/members/{user_id}")
def remove_group_member(group_id: int, user_id: int, requester_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, requester_id)
    group = member_group(db, actor, group_id)
    db.refresh(group, with_for_update=True)
    if group.creator_id != actor.id and user_id != actor.id:
        raise HTTPException(403, "Only the group owner can remove another member.")
    if group.creator_id == user_id:
        raise HTTPException(409, "Transfer ownership or delete the group before leaving.")

    mem = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if mem:
        db.delete(mem)
        db.commit()

    return {"status": "removed", "group_id": group_id, "user_id": user_id}


@app.post("/api/groups/{group_id}/transfer")
def transfer_group(group_id: int, payload: GroupTransferRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    group = owned_group(db, actor, group_id)
    new_owner = db.query(User).filter_by(id=payload.new_owner_id).first()
    if new_owner is None or bool(new_owner.is_reviewer) != bool(actor.is_reviewer):
        raise HTTPException(404, "New owner not found")
    if not db.query(GroupMember.id).filter_by(group_id=group_id, user_id=payload.new_owner_id).first():
        raise HTTPException(400, "The new owner must already belong to the group.")
    group.creator_id = payload.new_owner_id
    db.commit()
    return {"status": "transferred", "group_id": group_id, "creator_id": group.creator_id}


@app.delete("/api/groups/{group_id}")
def delete_group(group_id: int, requester_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, requester_id)
    group = owned_group(db, actor, group_id)

    # Delete all member associations first
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    # Delete the group
    db.delete(group)
    db.commit()

    return {"status": "deleted", "group_id": group_id}


@app.get("/api/groups/{group_id}/leaderboard", response_model=LeaderboardResponse)
def get_group_leaderboard(
    group_id: int,
    user_id: Optional[int] = Query(None),
    sort_by: str = Query("points", pattern="^(points|streak)$"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user_id = actor.id
    group = member_group(db, actor, group_id)

    users = (
        db.query(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return _compute_leaderboard(db, users, requester_id=user_id, sort_by=sort_by, limit=limit)


@app.post("/api/kudos/kudos-all")
def kudos_all_users(payload: KudosAllRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, payload.from_user_id)
    require_social_participant(actor)
    from_id = payload.from_user_id
    targets = sorted({tid for tid in (payload.target_user_ids or []) if tid != actor.id})
    if len(targets) > 100:
        raise HTTPException(400, "Choose at most 100 users.")
    if targets and db.query(User.id).filter(User.id.in_(targets), User.is_reviewer.is_(False)).count() != len(targets):
        raise HTTPException(400, "One or more target accounts no longer exist.")
    if not targets:
        return {"status": "ok", "updated_count": 0}

    now = datetime.utcnow()

    existing_kudos = (
        db.query(Kudos)
        .filter(Kudos.from_user_id == from_id, Kudos.to_user_id.in_(targets))
        .all()
    )
    existing_map = {k.to_user_id: k for k in existing_kudos}

    updated = 0
    for tid in targets:
        k = existing_map.get(tid)
        if k:
            k.created_at = now
            updated += 1
        else:
            new_k = Kudos(from_user_id=from_id, to_user_id=tid, created_at=now)
            db.add(new_k)
            updated += 1

    db.commit()
    return {"status": "ok", "updated_count": updated}


@app.post("/api/kudos/{to_user_id}")
def toggle_kudos(to_user_id: int, payload: KudosToggleRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, payload.from_user_id)
    require_social_participant(actor)
    from_id = payload.from_user_id
    if from_id == to_user_id:
        raise HTTPException(status_code=400, detail="You cannot give kudos to yourself.")

    to_user = db.query(User).filter(User.id == to_user_id).first()
    if not to_user or to_user.is_reviewer:
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
            existing.created_at = datetime.utcnow()
            db.commit()
            status = "renewed"
    else:
        k = Kudos(from_user_id=from_id, to_user_id=to_user_id, created_at=datetime.utcnow())
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    diff = now - (dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt)
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
async def get_user_recent_solves(user_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), actor: User = Depends(current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    require_visible_profile(actor, user)

    # Activity is the latest observed acceptance, including a repeat. The unique
    # solve/award ledger and its first-solve timestamp remain unchanged.
    from .models import AcceptedSubmission
    from .timekeeping import utc_now
    latest = db.query(AcceptedSubmission.solve_id.label("solve_id"),
        func.max(AcceptedSubmission.accepted_at).label("accepted_at")).filter(
        AcceptedSubmission.user_id == user_id, AcceptedSubmission.accepted_at <= utc_now()
    ).group_by(AcceptedSubmission.solve_id).subquery()
    activity_at = func.coalesce(latest.c.accepted_at, Solve.solved_at)
    solves = db.query(Solve, activity_at.label("activity_at")).outerjoin(
        latest, latest.c.solve_id == Solve.id).filter(Solve.user_id == user_id, or_(
        and_(Solve.platform == "leetcode", Solve.account_version == user.leetcode_account_version,
             or_(func.lower(Solve.source_handle) == user.leetcode_username.lower(),
                 and_(Solve.source_handle.is_(None), user.leetcode_account_version == 0))),
        and_(Solve.platform == "codeforces", Solve.account_version == user.codeforces_account_version,
             user.codeforces_username is not None,
             or_(func.lower(Solve.source_handle) == (user.codeforces_username or "").lower(),
                 and_(Solve.source_handle.is_(None), user.codeforces_account_version == 0)))
    )).order_by(activity_at.desc(), Solve.id.desc()).limit(limit).all()

    results = []
    for s, accepted_at in solves:
        if not current_account(user, s):
            continue
        breakdown_data = stored_breakdown(db, s)
        points_val = s.points_earned or 0

        results.append(
            RecentSolveSchema(
                title_slug=s.title_slug,
                title=s.title or s.title_slug.replace("-", " ").title(),
                solved_at=accepted_at.replace(tzinfo=timezone.utc),
                relative_time=_time_ago(accepted_at),
                leetcode_url=solve_url(s), problem_url=solve_url(s), platform=s.platform,
                source_handle=s.source_handle, source_submission_id=s.source_submission_id,
                problem_rating=s.problem_rating, scoring_version=s.scoring_version,
                points_earned=points_val,
                first_solve_verified=s.first_solve_verified,
                first_solve_basis=s.first_solve_basis,
                first_solve_at=s.first_solve_at.replace(tzinfo=timezone.utc) if s.first_solve_at else None,
                breakdown=PointBreakdownSchema(**breakdown_data),
            )
        )

        if len(results) >= limit:
            break
    return results


@app.get("/api/users/{user_id}/codeforces-solves")
def codeforces_solved_questions(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    require_visible_profile(actor, user)
    slugs = [row[0] for row in db.query(Solve.title_slug).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all()]
    return {"handle": user.codeforces_username, "slugs": slugs, "synced_at": user.codeforces_last_sync.replace(tzinfo=timezone.utc) if user.codeforces_last_sync else None}


@app.get("/api/feed/recent-solves", response_model=List[ActivityFeedItemSchema])
async def get_global_recent_solves(limit: int = Query(15, ge=1, le=100), db: Session = Depends(get_db), actor: User = Depends(current_user)):
    """Returns the latest solved questions from all users across the platform in chronological order."""
    solves = (
        db.query(Solve, User)
        .join(User, Solve.user_id == User.id)
        .filter(User.is_reviewer.is_(False))
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
                user_handle=solve.source_handle or user.leetcode_username,
                title=title,
                title_slug=solve.title_slug,
                solved_at=solve.solved_at.replace(tzinfo=timezone.utc),
                relative_time=_time_ago(solve.solved_at),
                leetcode_url=solve_url(solve), problem_url=solve_url(solve), platform=solve.platform,
                source_handle=solve.source_handle, source_submission_id=solve.source_submission_id,
                problem_rating=solve.problem_rating, scoring_version=solve.scoring_version,
            )
        )
    return feed


def claim_admin_operation(db: Session, key: str, *, repeat_after: int | None = None):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = db.query(AdminOperation).filter_by(operation_key=key).with_for_update().first()
    if row:
        if row.state == "running":
            raise HTTPException(409, "This job is already running or needs operator recovery.")
        if repeat_after is None:
            raise HTTPException(409, "This release job was already submitted. Review its outcome before retrying.")
        if (now - row.started_at).total_seconds() < repeat_after:
            raise HTTPException(429, "Wait before starting another all-user sync.")
        row.state, row.started_at, row.finished_at = "running", now, None
    else:
        db.add(AdminOperation(operation_key=key, state="running", started_at=now))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This job was already submitted.")
    logger.info("Administrative job started: %s", key)


def finish_admin_operation(key: str, state: str):
    with SessionLocal() as db:
        row = db.query(AdminOperation).filter_by(operation_key=key).first()
        if row:
            row.state = state
            row.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
    logger.info("Administrative job finished: %s (%s)", key, state)


@app.post("/api/admin/poll-now", dependencies=[Depends(verify_admin_secret)])
async def poll_now(db: Session = Depends(get_db)):
    claim_admin_operation(db, "poll-all", repeat_after=60)
    try:
        results = await poll_all_users()
    except Exception:
        finish_admin_operation("poll-all", "failed")
        raise HTTPException(503, "All-user sync failed. Review the job status before retrying.")
    finish_admin_operation("poll-all", "completed")
    return {"status": "completed", "accounts_polled": len(results)}


@app.post("/api/admin/reset-db", dependencies=[Depends(verify_admin_secret)])
def reset_db(db: Session = Depends(get_db)):
    """Clears all database records for fresh user registrations."""
    if db.query(User.id).filter(User.is_reviewer.is_(True)).first():
        raise HTTPException(409, "Persistent review accounts are configured. Use targeted account cleanup instead.")
    clear_tracking(db)
    db.query(Kudos).delete()
    db.query(PlatformActivity).delete()
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


@app.post("/api/admin/init-user-dates", dependencies=[Depends(verify_admin_secret)])
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
    require_mutable_identity(user)

    if db.query(Group.id).filter(Group.creator_id == user_id).first():
        raise HTTPException(409, "Resolve owned groups before deleting this account.")
    from .models import UserSyncJob
    db.query(UserSyncJob).filter_by(user_id=user_id).delete()
    clear_tracking(db, user_id)
    db.query(AccountProgress).filter_by(user_id=user_id).delete()
    db.query(Kudos).filter((Kudos.from_user_id == user_id) | (Kudos.to_user_id == user_id)).delete()
    db.query(Solve).filter(Solve.user_id == user_id).delete()
    db.query(DailyActivity).filter(DailyActivity.user_id == user_id).delete()
    db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id).delete()
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
    <updatecheck codebase='https://codestreak-api.onrender.com/downloads/leetstreak.crx' version='1.0.0' />
  </app>
</gupdate>"""
    return Response(content=xml_content, media_type="application/xml")


@app.get("/api/extension/version")
def get_extension_version():
    """Serves latest extension version info for in-app update notification banner."""
    return {
        "latest_version": "1.0.0",
        "latest_commit": "09d1cfc",
        "min_supported_version": "1.0.0",
        "release_notes": "Cleaned up username guide instructions and layout with clear steps and spacious formatting.",
        "download_url": "https://codestreak-api.onrender.com/downloads/leetstreak.zip",
        "crx_url": "https://codestreak-api.onrender.com/downloads/leetstreak.crx"
    }


@app.get("/downloads/leetstreak.zip")
def download_extension_zip():
    """Serves downloadable leetstreak.zip file."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "leetstreak.zip"),
        os.path.join(os.path.dirname(__file__), "..", "leetstreak.zip"),
        os.path.join(os.path.dirname(__file__), "..", "..", "leetstreak.zip"),
        "/app/app/leetstreak.zip",
        "/app/leetstreak.zip",
    ]
    for zip_path in possible_paths:
        if os.path.exists(zip_path):
            return FileResponse(zip_path, filename="leetstreak.zip", media_type="application/zip")
    return {"error": "Extension package file not found"}


async def send_and_update_user_commit(
    user_id: int,
    to_email: str,
    username: str,
    commit_id: str,
    release_notes: str,
    download_url: str
):
    """Sends update notification email and updates user's last_notified_commit in DB upon success."""
    success = await send_update_notification_email(
        to_email=to_email,
        username=username,
        commit_id=commit_id,
        release_notes=release_notes,
        download_url=download_url
    )
    if success:
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            if u:
                u.last_notified_commit = commit_id
                db.commit()
                logging.info("Release notification accepted for account %d", user_id)
        except Exception:
            db.rollback()
            logging.error("Release delivery state could not be saved for account %d", user_id)
            return False
        finally:
            db.close()
    return success


async def broadcast_release(release_id: str, recipients: list[int]):
    notice = RELEASE_NOTICES[release_id]
    accepted = True
    try:
        for user_id in recipients:
            with SessionLocal() as db:
                user = db.query(User).filter_by(id=user_id).first()
                if not user or user.last_notified_commit == release_id:
                    continue
                address, name = user.email, (user.name or "Coder").strip() or "Coder"
            result = await send_and_update_user_commit(user_id, address, name, release_id, notice.notes, notice.download_url)
            accepted = bool(result) and accepted
        finish_admin_operation("broadcast:" + release_id, "completed" if accepted else "failed")
    except Exception:
        finish_admin_operation("broadcast:" + release_id, "failed")
        logger.error("Release broadcast interrupted; operator review required.")


@app.post("/api/admin/broadcast-update-email", dependencies=[Depends(verify_admin_secret)])
def broadcast_update_email(payload: ReleaseBroadcastRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.release_id not in RELEASE_NOTICES:
        raise HTTPException(400, "Choose a reviewed release ID.")
    ids = [row[0] for row in db.query(User.id).filter(User.is_reviewer.is_(False), User.email.isnot(None), User.email != "", User.last_notified_commit != payload.release_id).all()]
    if payload.dry_run:
        return {"status": "preview", "eligible_accounts": len(ids), "release_id": payload.release_id}
    claim_admin_operation(db, "broadcast:" + payload.release_id)
    background_tasks.add_task(broadcast_release, payload.release_id, ids)
    return {"status": "queued", "eligible_accounts": len(ids), "release_id": payload.release_id}


# ==========================================================================
# 🌐 DYNAMIC BACKEND-DRIVEN OTA APP CONFIG & MENU ENDPOINT
# ==========================================================================
DEFAULT_WHATSAPP_SHARE_URL = (
    "https://api.whatsapp.com/send?text="
    "Check%20out%20LeetStreak%20to%20track%20your%20LeetCode%20daily%20streak%20and%20compete%20on%20leaderboards%20with%20friends%21%20%F0%9F%94%A5%0A%0A"
    "%F0%9F%93%A5%20Download%20Extension%20%28.zip%29%3A%0Ahttps%3A//codestreak-api.onrender.com/downloads/leetstreak.zip%0A%0A"
    "%F0%9F%9B%A0%EF%B8%8F%20Quick%2030-Sec%20Install%3A%0A1.%20Unzip%20leetstreak.zip%0A2.%20Open%20chrome%3A//extensions%20%26%20enable%20Developer%20mode%0A3.%20Click%20%22Load%20unpacked%22%20and%20select%20the%20unzipped%20folder%0A%0A"
    "%F0%9F%93%96%20Full%20Setup%20Guide%3A%0Ahttps%3A//github.com/youngcaptainkeos/Leetcode-Leetstreak%23readme%0A"
)


@app.get("/api/config/app", response_model=AppConfigResponse)
def get_app_config():
    """Serves dynamic over-the-air app configuration, feature flags, announcements, dynamic menus, and share URLs."""
    return AppConfigResponse(
        version="1.0.0",
        maintenance_mode=False,
        announcement=None,
        whatsapp_share_url=DEFAULT_WHATSAPP_SHARE_URL,
        menu_items=[
            DynamicMenuItem(id="dashboard", label="Dashboard", icon="📊", type="tab", enabled=True),
            DynamicMenuItem(id="groups", label="Groups", icon="👥", type="tab", enabled=True),
            DynamicMenuItem(id="coffee", label="Buy Me a Coffee", icon="☕", type="modal", enabled=True),
        ]
    )




# The website is built into backend/web locally and /app/web in the container.
# Keep page routes explicit so unknown API endpoints still return their usual 404.
WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "web"
app.mount("/web-assets", StaticFiles(directory=str(WEB_DIRECTORY / "assets"), check_dir=False), name="web-assets")


@app.get("/", include_in_schema=False)
@app.get("/home", include_in_schema=False)
@app.get("/login", include_in_schema=False)
@app.get("/register", include_in_schema=False)
@app.get("/forgot-password", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def website_page():
    index = WEB_DIRECTORY / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="Website assets are not built. Run npm --prefix web run build.")
    return FileResponse(index, media_type="text/html", headers={"Cache-Control": "no-cache"})
