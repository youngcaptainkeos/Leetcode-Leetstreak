"""Persisted abuse limits and one-time recovery verifiers; no raw identity logs."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .config import JWT_SECRET
from .models import AuthLimit, User


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def consume_limit(db, purpose: str, identifier: str, maximum: int, seconds: int):
    key = hmac.new(JWT_SECRET.encode(), (purpose + ":" + identifier).encode(), hashlib.sha256).hexdigest()
    now = utcnow()
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(AuthLimit).values(bucket_key=key, window_started_at=now, attempts=0).on_conflict_do_nothing(index_elements=["bucket_key"]))
    bucket = db.query(AuthLimit).filter_by(bucket_key=key).populate_existing().with_for_update().one()
    if now - bucket.window_started_at >= timedelta(seconds=seconds):
        bucket.window_started_at, bucket.attempts = now, 0
    if bucket.attempts >= maximum:
        db.rollback()
        raise HTTPException(429, "Too many attempts. Please try again later.", headers={"Retry-After": str(seconds)})
    bucket.attempts += 1
    db.commit()


def recovery_account(db, identifier: str):
    # Exact normalized equality, not SQL LIKE wildcards from user input.
    from sqlalchemy import func
    email_match = db.query(User).filter(func.lower(User.email) == identifier).first()
    if email_match:
        return email_match
    matches = db.query(User).filter(func.lower(User.leetcode_username) == identifier).limit(2).all()
    return matches[0] if len(matches) == 1 else None


def otp_verifier(user_id: int, request_id: str, code: str) -> str:
    message = f"password-reset:{user_id}:{request_id}:{code}"
    return hmac.new(JWT_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()


def clear_reset(user):
    user.reset_otp = None
    user.reset_otp_hash = None
    user.otp_request_id = None
    user.otp_expires_at = None
    user.otp_attempts = 0
