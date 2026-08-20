from datetime import datetime, date as date_type

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    leetcode_username = Column(String(80), nullable=False, index=True)
    email = Column(String(120), nullable=False, unique=True, index=True)
    password_hash = Column(String(200), nullable=True)
    reset_otp = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    easy_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    hard_count = Column(Integer, default=0)
    official_streak = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    daily_activity = relationship("DailyActivity", back_populates="user", cascade="all, delete-orphan")
    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class DailyActivity(Base):
    """One row per user per calendar date they solved >=1 problem."""
    __tablename__ = "daily_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    problems_solved = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="daily_activity")

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)


class Solve(Base):
    """
    Dedup ledger: one row per (user, problem) the first time we ever saw it
    accepted.
    """
    __tablename__ = "solves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title_slug = Column(String(200), nullable=False)
    title = Column(String(300), nullable=True)
    solved_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="solves")

    __table_args__ = (UniqueConstraint("user_id", "title_slug", name="uq_user_problem"),)


class Group(Base):
    """Friend Group with unique invite code."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """Junction table for Group members."""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)


class Kudos(Base):
    """Thumbs up kudos sent between users with 24-hour expiration."""
    __tablename__ = "kudos"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_kudos_pair"),)

