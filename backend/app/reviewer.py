"""Persistent, operator-provisioned store review login; no public signup bypass."""
import os
import re

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from .models import User
from .recovery import clear_reset
from .timekeeping import utc_now


def provision_reviewer(engine):
    """Idempotent startup provisioning from private service configuration only.

    No raw password is deployed. Rotation requires changing the configured hash;
    a normal account can never be silently converted into a reviewer account.
    """
    email = os.getenv("REVIEWER_EMAIL", "").strip().lower()
    password_hash = os.getenv("REVIEWER_PASSWORD_HASH", "").strip()
    handle = os.getenv("REVIEWER_LEETCODE_USERNAME", "").strip()
    if not any((email, password_hash, handle)):
        return
    if (not re.fullmatch(r"[^\s@]{1,64}@[^\s@]{1,100}\.[^\s@]+", email)
            or len(email) > 120
            or not re.fullmatch(r"[0-9a-f]{32}\$[0-9a-f]{64}", password_hash)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", handle)):
        raise RuntimeError("Review account configuration is incomplete or invalid.")
    with Session(bind=engine) as db, db.begin():
        if engine.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(72635002)"))
        user = db.query(User).filter(func.lower(User.email) == email).with_for_update().first()
        if user is None:
            db.add(User(email=email, password_hash=password_hash,
                        name="Chrome Web Store Reviewer", leetcode_username=handle,
                        is_reviewer=True, created_at=utc_now()))
        elif not user.is_reviewer:
            raise RuntimeError("Review account configuration conflicts with an existing account.")
        elif user.leetcode_username.casefold() != handle.casefold():
            raise RuntimeError("Review account handle changes require an explicit account migration.")
        elif user.password_hash != password_hash:
            user.password_hash = password_hash
            user.session_version += 1
            clear_reset(user)


def require_mutable_identity(user):
    if user.is_reviewer:
        raise HTTPException(403, "This dedicated review login is managed by the publisher. Its credentials and coding accounts cannot be changed or deleted.")


def require_visible_profile(actor, user):
    if user is None or (user.is_reviewer and actor.id != user.id):
        raise HTTPException(404, "User not found")


def require_social_participant(actor):
    if actor.is_reviewer:
        raise HTTPException(403, "Review accounts can view rankings but cannot send kudos to real participants.")


def require_group_scope(db, actor, group):
    owner = db.query(User).filter_by(id=group.creator_id).first()
    if bool(owner and owner.is_reviewer) != bool(actor.is_reviewer):
        raise HTTPException(404, "Group not found")
