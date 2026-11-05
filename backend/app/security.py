"""Shared account and group authorization. IDs in a request never establish identity."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .auth import decode_access_token
from .database import get_db
from .models import User, Group, GroupMember

bearer = HTTPBearer(auto_error=False)


def current_user(
    credential: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    denied = HTTPException(401, "Please sign in again.", headers={"WWW-Authenticate": "Bearer"})
    if not credential or credential.scheme.lower() != "bearer":
        raise denied
    try:
        claims = decode_access_token(credential.credentials)
        user = db.query(User).filter(User.id == int(claims["sub"])).first()
        if not user or claims.get("ver", 0) != getattr(user, "session_version", 0):
            raise denied
        return user
    except (ValueError, TypeError, KeyError, OverflowError):
        raise denied


def require_self(actor: User, requested_id: int | None) -> None:
    if requested_id is not None and actor.id != requested_id:
        raise HTTPException(403, "You can only manage your own account.")


def member_group(db: Session, actor: User, group_id: int) -> Group:
    member = db.query(GroupMember.id).filter_by(group_id=group_id, user_id=actor.id).first()
    if not member:
        raise HTTPException(403, "Group membership required.")
    group = db.query(Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(404, "Group not found.")
    return group


def owned_group(db: Session, actor: User, group_id: int) -> Group:
    group = member_group(db, actor, group_id)
    db.refresh(group, with_for_update=True)
    if group.creator_id != actor.id:
        raise HTTPException(403, "Only the group owner can perform this action.")
    return group
