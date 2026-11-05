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
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS, ADMIN_SECRET
from .database import Base, engine, get_db, SessionLocal
from .models import AdminOperation, User, PlatformActivity, DailyActivity, Group, GroupMember, Solve, Kudos, DailyChallenge, UserProgress, UserCustomPlan
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from .email_service import send_otp_email, send_update_notification_email
from .schemas import (
    RegisterRequest, RegisterResponse, DashboardResponse, DayCount,
    LeaderboardResponse, LeaderboardEntry, GroupCreateRequest, GroupJoinRequest,
    GroupResponse, GroupListResponse, GroupMemberSchema, RecentSolveSchema, PointBreakdownSchema,
    LoginRequest, ForgotPasswordInitiateRequest, ForgotPasswordVerifyRequest,
    KudosToggleRequest, KudosAllRequest, UpdateUsernameRequest, UpdateSettingsRequest, ActivityFeedItemSchema,
    DynamicMenuItem, AppConfigResponse, DeleteAccountRequest, SyncRequest, UpdateCodeforcesRequest, GroupTransferRequest, ReleaseBroadcastRequest, ChangePasswordRequest,
    StudyPlanPayload, ProgressUpdateRequest, ProgressResponse,
    InitiateVerificationRequest, InitiateVerificationResponse,
    ConfirmVerificationRequest, ConfirmVerificationResponse,
    VerificationStatusResponse, PlatformVerificationStatus,
)
from .streak import current_streak
from .timekeeping import IST, ist_today, week_start as product_week_start, month_start as product_month_start, period_bounds, utc_now
from .scheduler import start_scheduler, poll_all_users, poll_user
from .leetcode_client import fetch_leetcode_user_data, fetch_today_daily_challenge_slug, fetch_problem_info, LeetCodeError, check_leetcode_profile_verification
from .point_calculator import compute_solve_points_breakdown, compute_codeforces_points_breakdown, recalculate_user_points
from .platforms import daily_counts, solve_url
from .codeforces_client import fetch_profile, CodeforcesError, check_codeforces_profile_verification
from .codeforces_sync import background_codeforces_sync, user_sync_lock
from .security import current_user, require_self, member_group, owned_group
from .releases import RELEASE_NOTICES
from .migrations import (
    run_all_migrations,
    migrate_core,
    migrate_platforms,
    migrate_auth,
    migrate_display_preference,
    migrate_tracking,
    migrate_progress,
    migrate_verification,
)
from .recovery import consume_limit, recovery_account, otp_verifier, clear_reset, utcnow
from .tracking import clear_tracking, capture_score_baseline


def verify_admin_secret(x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret")):
    if len(ADMIN_SECRET.encode("utf-8")) < 32 or not x_admin_secret or not secrets.compare_digest(x_admin_secret.encode("utf-8"), ADMIN_SECRET.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Secret Header")
    return True

from sqlalchemy import text, func

logging.basicConfig(level=logging.INFO)

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
    run_all_migrations(engine)
    _scheduler = start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    global _scheduler
    if _scheduler:
        try:
            if _scheduler.running:
                _scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning("Scheduler shutdown warning: %s", e)
        finally:
            _scheduler = None



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
        created_at=datetime.now(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email or Codeforces handle is already registered.")
    db.refresh(user)

    # Ingest full history
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
    if not user:
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
    if not user:
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
async def sync_user(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    solves_added = await poll_user(db, user)
    return {"status": "synced", "user_id": user_id, "new_solves": solves_added}


@app.put("/api/users/{user_id}/leetcode-username")
async def update_leetcode_username(user_id: int, payload: UpdateUsernameRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
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

    if new_username.lower() != (user.leetcode_username or "").lower():
        capture_score_baseline(db, user.id)
        user.leetcode_account_version += 1
        user.leetcode_verified_at = None
        clear_tracking(db, user_id, "leetcode")
        db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "leetcode").delete()
        db.query(DailyActivity).filter(DailyActivity.user_id == user_id).delete()
        user.easy_count = 0
        user.medium_count = 0
        user.hard_count = 0
        user.official_streak = 0
        user.leetcode_history_state = "partial"
        user.leetcode_history_gap = True

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


@app.put("/api/users/{user_id}/codeforces-username")
async def update_codeforces_username(user_id: int, payload: UpdateCodeforcesRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
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
    owner = db.query(User).filter(func.lower(User.codeforces_username) == handle.lower(), User.id != user_id).first()
    if owner:
        if owner.codeforces_verified_at:
            raise HTTPException(status_code=409, detail="That Codeforces handle is already connected and verified on another account.")
        raise HTTPException(status_code=409, detail="That Codeforces handle is claimed by an unverified account. Initiate verification to prove ownership and claim this handle.")
    async with user_sync_lock(user_id):
        db.refresh(user, with_for_update=True)
        if not user.codeforces_username or user.codeforces_username.lower() != handle.lower():
            clear_tracking(db, user_id, "codeforces")
            db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").delete()
            db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id, PlatformActivity.platform == "codeforces").delete()
            user.codeforces_last_sync = None
            user.codeforces_last_full_sync = None
            user.codeforces_verified_at = None
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


@app.post("/api/users/{user_id}/verify-handle/initiate", response_model=InitiateVerificationResponse)
async def initiate_handle_verification(
    user_id: int,
    payload: InitiateVerificationRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    platform = payload.platform.lower()
    target_handle = (payload.handle or "").strip()
    is_claim_recovery = False

    if platform == "leetcode":
        if not target_handle:
            target_handle = user.leetcode_username
        if not target_handle:
            raise HTTPException(status_code=400, detail="No LeetCode username linked to your account.")
        if target_handle.lower() == (user.leetcode_username or "").lower() and user.leetcode_verified_at:
            raise HTTPException(status_code=400, detail="Your LeetCode account is already verified.")

        owner = db.query(User).filter(func.lower(User.leetcode_username) == target_handle.lower(), User.id != user_id).first()
        if owner:
            if owner.leetcode_verified_at:
                raise HTTPException(status_code=409, detail="That LeetCode handle is already claimed and verified by another user.")
            is_claim_recovery = True

        token = f"codestreak-verify-{secrets.token_hex(6)}"
        expires_at = utc_now() + timedelta(minutes=15)
        user.leetcode_verification_token = token
        user.leetcode_verification_expires_at = expires_at.replace(tzinfo=None)
        user.leetcode_pending_handle = target_handle
        db.commit()

        instructions = (
            f"Add the verification code '{token}' into your LeetCode profile 'Summary' / 'About Me' or Name "
            f"(https://leetcode.com/profile/lab/), save your profile, and then click 'Confirm Verification'."
        )
        return InitiateVerificationResponse(
            platform="leetcode",
            handle=target_handle,
            token=token,
            expires_at=expires_at,
            instructions=instructions,
            is_claim_recovery=is_claim_recovery,
        )

    elif platform == "codeforces":
        if not target_handle:
            target_handle = user.codeforces_username
        if not target_handle:
            raise HTTPException(status_code=400, detail="No Codeforces handle specified or linked to your account.")
        if user.codeforces_username and target_handle.lower() == user.codeforces_username.lower() and user.codeforces_verified_at:
            raise HTTPException(status_code=400, detail="Your Codeforces account is already verified.")

        owner = db.query(User).filter(func.lower(User.codeforces_username) == target_handle.lower(), User.id != user_id).first()
        if owner:
            if owner.codeforces_verified_at:
                raise HTTPException(status_code=409, detail="That Codeforces handle is already claimed and verified by another user.")
            is_claim_recovery = True

        token = f"codestreak-verify-{secrets.token_hex(6)}"
        expires_at = utc_now() + timedelta(minutes=15)
        user.codeforces_verification_token = token
        user.codeforces_verification_expires_at = expires_at.replace(tzinfo=None)
        user.codeforces_pending_handle = target_handle
        db.commit()

        instructions = (
            f"Add the verification code '{token}' into your Codeforces 'Organization' or 'First Name' "
            f"(https://codeforces.com/settings/social), save changes, and then click 'Confirm Verification'."
        )
        return InitiateVerificationResponse(
            platform="codeforces",
            handle=target_handle,
            token=token,
            expires_at=expires_at,
            instructions=instructions,
            is_claim_recovery=is_claim_recovery,
        )


@app.post("/api/users/{user_id}/verify-handle/confirm", response_model=ConfirmVerificationResponse)
async def confirm_handle_verification(
    user_id: int,
    payload: ConfirmVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    platform = payload.platform.lower()
    now_utc = utc_now()

    if platform == "leetcode":
        token = user.leetcode_verification_token
        expires_at = user.leetcode_verification_expires_at
        handle = user.leetcode_pending_handle or user.leetcode_username
        if not token or not expires_at or not handle:
            raise HTTPException(status_code=400, detail="No LeetCode verification in progress. Please click 'Verify' to initiate one.")
        if now_utc.replace(tzinfo=None) > expires_at:
            raise HTTPException(status_code=400, detail="LeetCode verification code has expired. Please initiate a new one.")

        try:
            matched = await check_leetcode_profile_verification(handle, token)
        except LeetCodeError as err:
            raise HTTPException(status_code=400, detail=f"LeetCode verification check failed: {err}")
        if not matched:
            raise HTTPException(
                status_code=400,
                detail=f"Verification code '{token}' not found on LeetCode profile for '{handle}'. Make sure you saved your profile changes and try again.",
            )

        owner = db.query(User).filter(func.lower(User.leetcode_username) == handle.lower(), User.id != user_id).first()
        if owner:
            owner.leetcode_username = f"claimed_{owner.id}_{secrets.token_hex(3)}"
            owner.leetcode_verified_at = None
            owner.leetcode_account_version += 1
            clear_tracking(db, owner.id, "leetcode")
            db.query(Solve).filter(Solve.user_id == owner.id, Solve.platform == "leetcode").delete()
            recalculate_user_points(owner, db)

        user.leetcode_username = handle
        user.leetcode_verified_at = now_utc.replace(tzinfo=None)
        user.leetcode_verification_token = None
        user.leetcode_verification_expires_at = None
        user.leetcode_pending_handle = None
        db.commit()

        background_tasks.add_task(poll_user, db, user)
        return ConfirmVerificationResponse(
            status="verified",
            platform="leetcode",
            handle=handle,
            verified_at=now_utc,
        )

    elif platform == "codeforces":
        token = user.codeforces_verification_token
        expires_at = user.codeforces_verification_expires_at
        handle = user.codeforces_pending_handle or user.codeforces_username
        if not token or not expires_at or not handle:
            raise HTTPException(status_code=400, detail="No Codeforces verification in progress. Please click 'Verify' to initiate one.")
        if now_utc.replace(tzinfo=None) > expires_at:
            raise HTTPException(status_code=400, detail="Codeforces verification code has expired. Please initiate a new one.")

        try:
            matched = await check_codeforces_profile_verification(handle, token)
        except CodeforcesError as err:
            raise HTTPException(status_code=400, detail=f"Codeforces verification check failed: {err}")
        if not matched:
            raise HTTPException(
                status_code=400,
                detail=f"Verification code '{token}' not found on Codeforces profile for '{handle}'. Make sure you saved changes in Settings -> Social and try again.",
            )

        owner = db.query(User).filter(func.lower(User.codeforces_username) == handle.lower(), User.id != user_id).first()
        if owner:
            owner.codeforces_username = None
            owner.codeforces_verified_at = None
            owner.codeforces_account_version += 1
            clear_tracking(db, owner.id, "codeforces")
            db.query(Solve).filter(Solve.user_id == owner.id, Solve.platform == "codeforces").delete()
            db.query(PlatformActivity).filter(PlatformActivity.user_id == owner.id, PlatformActivity.platform == "codeforces").delete()
            recalculate_user_points(owner, db)

        user.codeforces_username = handle
        user.codeforces_verified_at = now_utc.replace(tzinfo=None)
        user.codeforces_linked_at = user.codeforces_linked_at or now_utc.replace(tzinfo=None)
        user.codeforces_verification_token = None
        user.codeforces_verification_expires_at = None
        user.codeforces_pending_handle = None
        db.commit()

        background_tasks.add_task(background_codeforces_sync, user_id)
        return ConfirmVerificationResponse(
            status="verified",
            platform="codeforces",
            handle=handle,
            verified_at=now_utc,
        )


@app.get("/api/users/{user_id}/verify-handle/status", response_model=VerificationStatusResponse)
def get_handle_verification_status(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(current_user),
):
    require_self(actor, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = utc_now().replace(tzinfo=None)
    lc_pending = bool(user.leetcode_verification_token and user.leetcode_verification_expires_at and now <= user.leetcode_verification_expires_at)
    cf_pending = bool(user.codeforces_verification_token and user.codeforces_verification_expires_at and now <= user.codeforces_verification_expires_at)

    return VerificationStatusResponse(
        user_id=user.id,
        leetcode=PlatformVerificationStatus(
            handle=user.leetcode_username,
            verified=user.leetcode_verified_at is not None,
            verified_at=user.leetcode_verified_at.replace(tzinfo=timezone.utc) if user.leetcode_verified_at else None,
            pending_token=lc_pending,
            expires_at=user.leetcode_verification_expires_at.replace(tzinfo=timezone.utc) if user.leetcode_verification_expires_at else None,
        ),
        codeforces=PlatformVerificationStatus(
            handle=user.codeforces_username,
            verified=user.codeforces_verified_at is not None,
            verified_at=user.codeforces_verified_at.replace(tzinfo=timezone.utc) if user.codeforces_verified_at else None,
            pending_token=cf_pending,
            expires_at=user.codeforces_verification_expires_at.replace(tzinfo=timezone.utc) if user.codeforces_verification_expires_at else None,
        ),
    )


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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password. Account deletion failed.")

    if db.query(Group.id).filter(Group.creator_id == actor.id).first():
        raise HTTPException(409, "Transfer ownership or delete your groups before deleting your account.")

    clear_tracking(db, user_id)
    db.query(UserProgress).filter(UserProgress.user_id == user_id).delete()
    db.query(UserCustomPlan).filter(UserCustomPlan.user_id == user_id).delete()
    db.query(GroupMember).filter(GroupMember.user_id == user_id).delete()
    db.query(DailyActivity).filter(DailyActivity.user_id == user_id).delete()
    db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id).delete()
    db.query(Solve).filter(Solve.user_id == user_id).delete()
    db.query(Kudos).filter((Kudos.from_user_id == user_id) | (Kudos.to_user_id == user_id)).delete()
    db.query(Group).filter(Group.creator_id == user_id).update({Group.creator_id: None})

    db.delete(user)
    db.commit()

    return {"status": "account_deleted", "message": "Account deleted successfully"}


@app.get("/api/users/{user_id}/progress", response_model=ProgressResponse)
def get_user_progress(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    prog = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
    if not prog:
        prog = UserProgress(
            user_id=user_id,
            followed_plans=[],
            hidden_plans=[],
            manual_solves=[],
            version=1,
            updated_at=utc_now(),
        )
        db.add(prog)
        db.commit()
        db.refresh(prog)

    custom_plans = db.query(UserCustomPlan).filter(UserCustomPlan.user_id == user_id).all()
    plans_data = [cp.plan_json if isinstance(cp.plan_json, dict) else {} for cp in custom_plans]

    return ProgressResponse(
        user_id=user_id,
        followed=prog.followed_plans or [],
        hidden=prog.hidden_plans or [],
        manual=prog.manual_solves or [],
        custom_plans=plans_data,
        version=prog.version,
        updated_at=prog.updated_at.isoformat() if prog.updated_at else None,
    )


@app.put("/api/users/{user_id}/progress", response_model=ProgressResponse)
def update_user_progress(user_id: int, payload: ProgressUpdateRequest, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    prog = db.query(UserProgress).filter(UserProgress.user_id == user_id).with_for_update().first()
    if not prog:
        prog = UserProgress(
            user_id=user_id,
            followed_plans=[],
            hidden_plans=[],
            manual_solves=[],
            version=1,
            updated_at=utc_now(),
        )
        db.add(prog)

    if payload.followed is not None:
        if len(payload.followed) > 1000 or any(len(s) > 100 for s in payload.followed):
            raise HTTPException(400, "Followed plans list exceeds allowed bounds.")
        prog.followed_plans = list(dict.fromkeys(payload.followed))

    if payload.hidden is not None:
        if len(payload.hidden) > 1000 or any(len(s) > 100 for s in payload.hidden):
            raise HTTPException(400, "Hidden plans list exceeds allowed bounds.")
        prog.hidden_plans = list(dict.fromkeys(payload.hidden))

    if payload.manual is not None:
        if len(payload.manual) > 10000 or any(len(s) > 200 for s in payload.manual):
            raise HTTPException(400, "Manual solves list exceeds allowed bounds.")
        prog.manual_solves = list(dict.fromkeys(payload.manual))

    prog.version += 1
    prog.updated_at = utc_now()
    db.commit()
    db.refresh(prog)

    custom_plans = db.query(UserCustomPlan).filter(UserCustomPlan.user_id == user_id).all()
    plans_data = [cp.plan_json if isinstance(cp.plan_json, dict) else {} for cp in custom_plans]

    return ProgressResponse(
        user_id=user_id,
        followed=prog.followed_plans or [],
        hidden=prog.hidden_plans or [],
        manual=prog.manual_solves or [],
        custom_plans=plans_data,
        version=prog.version,
        updated_at=prog.updated_at.isoformat() if prog.updated_at else None,
    )


@app.post("/api/users/{user_id}/plans")
def save_custom_plan(user_id: int, payload: StudyPlanPayload, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    existing_plan = db.query(UserCustomPlan).filter_by(user_id=user_id, slug=payload.slug).first()
    if not existing_plan:
        count = db.query(func.count(UserCustomPlan.id)).filter(UserCustomPlan.user_id == user_id).scalar()
        if count >= 50:
            raise HTTPException(400, "Maximum of 50 custom plans reached.")

    if len(payload.planSubGroups) > 200:
        raise HTTPException(400, "Plan subgroups cannot exceed 200.")
    total_questions = sum(len(g.questions) for g in payload.planSubGroups)
    if total_questions > 1000:
        raise HTTPException(400, "A study plan cannot exceed 1000 questions.")

    plan_dict = payload.model_dump()

    if existing_plan:
        existing_plan.name = payload.name
        existing_plan.source = payload.source
        existing_plan.source_url = payload.sourceUrl
        existing_plan.plan_json = plan_dict
        existing_plan.updated_at = utc_now()
    else:
        new_plan = UserCustomPlan(
            user_id=user_id,
            slug=payload.slug,
            name=payload.name,
            source=payload.source,
            source_url=payload.sourceUrl,
            plan_json=plan_dict,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(new_plan)

    prog = db.query(UserProgress).filter(UserProgress.user_id == user_id).with_for_update().first()
    if not prog:
        prog = UserProgress(
            user_id=user_id,
            followed_plans=[payload.slug],
            hidden_plans=[],
            manual_solves=[],
            version=1,
            updated_at=utc_now(),
        )
        db.add(prog)
    else:
        followed = list(prog.followed_plans or [])
        if payload.slug not in followed:
            followed.append(payload.slug)
        hidden = [s for s in (prog.hidden_plans or []) if s != payload.slug]
        prog.followed_plans = followed
        prog.hidden_plans = hidden
        prog.version += 1
        prog.updated_at = utc_now()

    db.commit()
    return plan_dict


@app.delete("/api/users/{user_id}/plans/{slug}")
def delete_custom_plan(user_id: int, slug: str, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    STARTER_PLANS = {"strivers-a2z", "top-sql-50", "top-interview-150", "leetcode-75"}

    db.query(UserCustomPlan).filter_by(user_id=user_id, slug=slug).delete()

    prog = db.query(UserProgress).filter(UserProgress.user_id == user_id).with_for_update().first()
    if not prog:
        prog = UserProgress(
            user_id=user_id,
            followed_plans=[],
            hidden_plans=[slug] if slug in STARTER_PLANS else [],
            manual_solves=[],
            version=1,
            updated_at=utc_now(),
        )
        db.add(prog)
    else:
        prog.followed_plans = [s for s in (prog.followed_plans or []) if s != slug]
        if slug in STARTER_PLANS:
            hidden = list(prog.hidden_plans or [])
            if slug not in hidden:
                hidden.append(slug)
            prog.hidden_plans = hidden
        else:
            prog.hidden_plans = [s for s in (prog.hidden_plans or []) if s != slug]
        prog.version += 1
        prog.updated_at = utc_now()

    db.commit()
    return {"ok": True, "slug": slug}


@app.post("/api/users/{user_id}/plans/restore-starters")
def restore_starter_plans(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    STARTER_PLANS = {"strivers-a2z", "top-sql-50", "top-interview-150", "leetcode-75"}
    prog = db.query(UserProgress).filter(UserProgress.user_id == user_id).with_for_update().first()
    if prog:
        prog.hidden_plans = [s for s in (prog.hidden_plans or []) if s not in STARTER_PLANS]
        prog.version += 1
        prog.updated_at = utc_now()
        db.commit()
    return {"ok": True}



def _active_dates(db: Session, user_id: int) -> set[date]:
    return set(daily_counts(db, [user_id])[user_id])


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
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = get_ist_today()
    week_start = get_current_week_start(today)
    month_start = get_current_month_start(today)

    active_dates = _active_dates(db, user_id)
    streak = current_streak(active_dates, today)

    combined = daily_counts(db, [user_id])[user_id]
    def total_since_date(start_date: date) -> int:
        return sum(count for day, count in combined.items() if day >= start_date)
    last_7 = [DayCount(date=today - timedelta(days=i), problems_solved=combined.get(today - timedelta(days=i), 0)) for i in range(6, -1, -1)]
    cf_count, cf_points = db.query(func.count(Solve.id), func.coalesce(func.sum(Solve.points_earned), 0)).filter(Solve.user_id == user_id, Solve.platform == "codeforces").one()

    today_row = next((d for d in last_7 if d.date == today), None)

    return DashboardResponse(
        leetcode_last_sync=user.leetcode_last_sync.replace(tzinfo=timezone.utc) if user.leetcode_last_sync else None,
        leetcode_history_state=user.leetcode_history_state,
        leetcode_history_gap=user.leetcode_history_gap,
        leetcode_verified=user.leetcode_verified_at is not None,
        leetcode_verified_at=user.leetcode_verified_at.replace(tzinfo=timezone.utc) if user.leetcode_verified_at else None,
        codeforces_last_sync=user.codeforces_last_sync.replace(tzinfo=timezone.utc) if user.codeforces_last_sync else None,
        codeforces_sync_error=user.codeforces_sync_error if actor.id == user_id else None,
        codeforces_verified=user.codeforces_verified_at is not None,
        codeforces_verified_at=user.codeforces_verified_at.replace(tzinfo=timezone.utc) if user.codeforces_verified_at else None,
        codeforces_count=cf_count, codeforces_points=round(float(cf_points), 2), leetcode_points=round((user.points or 0) - round(float(cf_points), 2), 2), points=user.points or 0,
        id=user.id,
        name=user.name,
        leetcode_username=user.leetcode_username,
        codeforces_username=user.codeforces_username,
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
    cf_stats = {row[0]: (row[1], float(row[2])) for row in db.query(Solve.user_id, func.count(Solve.id), func.coalesce(func.sum(Solve.points_earned), 0)).filter(Solve.user_id.in_(user_ids), Solve.platform == "codeforces").group_by(Solve.user_id).all()}

    raw = []
    for user in users:
        dates = combined[user.id]
        active_dates = set(dates)
        streak = current_streak(active_dates, today)
        week_rows = {day: count for day, count in dates.items() if week_start <= day <= today}
        weekly_total = sum(week_rows.values())
        active_days_this_week = len(week_rows)
        consistency = (active_days_this_week / days_in_week_so_far) * 100
        is_active_today = today in active_dates
        points = int(round(user.points or 0.0))
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
            leetcode_verified=r["user"].leetcode_verified_at is not None,
            codeforces_username=r["user"].codeforces_username,
            codeforces_verified=r["user"].codeforces_verified_at is not None,
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
    users = db.query(User).all()
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
        .all()
    )

    group_members_map = defaultdict(list)
    for g_id, user_obj in all_memberships:
        group_members_map[g_id].append(
            GroupMemberSchema(
                id=user_obj.id,
                name=user_obj.name,
                leetcode_username=user_obj.leetcode_username,
                leetcode_verified=user_obj.leetcode_verified_at is not None,
                codeforces_username=user_obj.codeforces_username,
                codeforces_verified=user_obj.codeforces_verified_at is not None,
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
    from_id = payload.from_user_id
    targets = sorted({tid for tid in (payload.target_user_ids or []) if tid != actor.id})
    if len(targets) > 100:
        raise HTTPException(400, "Choose at most 100 users.")
    if targets and db.query(User.id).filter(User.id.in_(targets)).count() != len(targets):
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

    today_daily_slug = await fetch_today_daily_challenge_slug()
    active_dates = _active_dates(db, user_id)
    daily_slugs_by_date = {
        r.date: r.title_slug.lower()
        for r in db.query(DailyChallenge).all()
    }

    db_changed = False
    results = []
    for s in solves:
        if s.platform == "codeforces":
            breakdown_data = compute_codeforces_points_breakdown(s.problem_rating, current_streak(active_dates, s.solved_at.replace(tzinfo=timezone.utc).astimezone(IST).date()))
            points_val = s.points_earned or 0
        else:
            diff = s.difficulty
            ac = s.ac_rate
            if not diff or ac is None:
                info = await fetch_problem_info(s.title_slug)
                diff = info.get("difficulty") or "Medium"
                ac = info.get("ac_rate")
                s.difficulty = diff
                s.ac_rate = ac
                db_changed = True

            solve_date = s.solved_at.date() if hasattr(s.solved_at, "date") else s.solved_at
            scoring_dates = active_dates if user.codeforces_linked_at and s.solved_at >= user.codeforces_linked_at else {row.date for row in db.query(DailyActivity).filter(DailyActivity.user_id == user_id, DailyActivity.problems_solved > 0).all()}
            streak_date = s.solved_at.replace(tzinfo=timezone.utc).astimezone(IST).date() if user.codeforces_linked_at and s.solved_at >= user.codeforces_linked_at else solve_date
            streak_on_date = current_streak(scoring_dates, streak_date)
            is_daily = (
                bool(getattr(s, "is_daily", False))
                or bool(today_daily_slug and solve_date == date.today() and s.title_slug.lower() == today_daily_slug.lower())
                or bool(solve_date in daily_slugs_by_date and s.title_slug.lower() == daily_slugs_by_date[solve_date])
            )
            if is_daily and not getattr(s, "is_daily", False):
                s.is_daily = True
                db_changed = True

            breakdown_data = compute_solve_points_breakdown(
                title_slug=s.title_slug,
                difficulty=diff,
                ac_rate=ac,
                is_daily=is_daily,
                streak_days=streak_on_date,
            )
            points_val = breakdown_data["points_earned"]
        # Report the ledger award; a read must never alter already counted points.
        breakdown_data["points_earned"] = s.points_earned or 0
        points_val = s.points_earned or 0

        results.append(
            RecentSolveSchema(
                title_slug=s.title_slug,
                title=s.title or s.title_slug.replace("-", " ").title(),
                solved_at=s.solved_at.replace(tzinfo=timezone.utc),
                relative_time=_time_ago(s.solved_at),
                leetcode_url=solve_url(s), problem_url=solve_url(s), platform=s.platform,
                source_handle=s.source_handle, source_submission_id=s.source_submission_id,
                problem_rating=s.problem_rating, scoring_version=s.scoring_version,
                points_earned=points_val,
                breakdown=PointBreakdownSchema(**breakdown_data),
            )
        )

    if db_changed:
        db.commit()

    return results


@app.get("/api/users/{user_id}/codeforces-solves")
def codeforces_solved_questions(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slugs = [row[0] for row in db.query(Solve.title_slug).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all()]
    return {"handle": user.codeforces_username, "slugs": slugs, "synced_at": user.codeforces_last_sync.replace(tzinfo=timezone.utc) if user.codeforces_last_sync else None}


@app.get("/api/feed/recent-solves", response_model=List[ActivityFeedItemSchema])
async def get_global_recent_solves(limit: int = Query(15, ge=1, le=100), db: Session = Depends(get_db), actor: User = Depends(current_user)):
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

    if db.query(Group.id).filter(Group.creator_id == user_id).first():
        raise HTTPException(409, "Resolve owned groups before deleting this account.")
    clear_tracking(db, user_id)
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
    ids = [row[0] for row in db.query(User.id).filter(User.email.isnot(None), User.email != "", User.last_notified_commit != payload.release_id).all()]
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
