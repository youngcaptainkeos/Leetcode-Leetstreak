from datetime import datetime, date as date_type

from sqlalchemy import (
    Column, Integer, BigInteger, Float, String, Date, DateTime, ForeignKey, UniqueConstraint, func, Boolean, JSON, Numeric, Index
)
from sqlalchemy.orm import relationship

from .database import Base
from .timekeeping import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    leetcode_account_version = Column(Integer, nullable=False, default=0, server_default="0")
    codeforces_account_version = Column(Integer, nullable=False, default=0, server_default="0")
    leetcode_last_sync = Column(DateTime, nullable=True)
    leetcode_history_state = Column(String(30), nullable=False, default="partial", server_default="partial")
    leetcode_history_gap = Column(Boolean, nullable=False, default=True, server_default="true")
    name = Column(String(80), nullable=False)
    leetcode_username = Column(String(80), nullable=False, index=True)
    email = Column(String(120), nullable=False, unique=True, index=True)
    password_hash = Column(String(200), nullable=True)
    reset_otp = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    session_version = Column(Integer, nullable=False, default=0, server_default="0")
    reset_otp_hash = Column(String(64), nullable=True)
    otp_request_id = Column(String(64), nullable=True)
    otp_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    otp_last_requested_at = Column(DateTime, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    codeforces_username = Column(String(80), nullable=True)
    codeforces_linked_at = Column(DateTime, nullable=True)
    codeforces_last_full_sync = Column(DateTime, nullable=True)
    codeforces_last_sync = Column(DateTime, nullable=True)
    codeforces_sync_error = Column(String(300), nullable=True)
    platform_activity = relationship("PlatformActivity", cascade="all, delete-orphan")
    easy_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    hard_count = Column(Integer, default=0)
    official_streak = Column(Integer, default=0)
    points = Column(Float, default=0.0)
    last_notified_commit = Column(String(40), default="legacy")
    global_leaderboard_enabled = Column(Boolean, default=True, nullable=False)
    show_global_leaderboard = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime, default=utc_now, server_default=func.now())

    daily_activity = relationship("DailyActivity", back_populates="user", cascade="all, delete-orphan")
    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class DailyActivity(Base):
    """One row per user per calendar date they solved >=1 problem."""
    __tablename__ = "daily_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    problems_solved = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="daily_activity")

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)


class Solve(Base):
    """
    Dedup ledger: one row per (user, namespaced problem). Codeforces problem
    IDs use cf-<contest>-<index>; legacy LeetCode slugs retain their original IDs.
    """
    __tablename__ = "solves"

    id = Column(Integer, primary_key=True, index=True)
    account_version = Column(Integer, nullable=False, default=0, server_default="0")
    first_solve_at = Column(DateTime, nullable=True, index=True)
    first_solve_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    score_components_state = Column(String(30), nullable=False, default="legacy", server_default="legacy")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False, default="leetcode", server_default="leetcode", index=True)
    source_handle = Column(String(80), nullable=True)
    source_submission_id = Column(BigInteger, nullable=True)
    problem_rating = Column(Float, nullable=True)
    problem_url = Column(String(500), nullable=True)
    scoring_version = Column(String(40), nullable=False, default="leetcode-v1", server_default="leetcode-v1")
    title_slug = Column(String(200), nullable=False)
    title = Column(String(300), nullable=True)
    difficulty = Column(String(20), nullable=True)
    ac_rate = Column(Float, nullable=True)
    solved_at = Column(DateTime, nullable=False, index=True)
    is_daily = Column(Boolean, default=False, nullable=False)
    points_earned = Column(Float, default=0.0)

    user = relationship("User", back_populates="solves")

    __table_args__ = (UniqueConstraint("user_id", "title_slug", name="uq_user_problem"),)


class DailyChallenge(Base):
    """
    Archive of official LeetCode Daily Challenge titleSlugs by date.
    """
    __tablename__ = "daily_challenges"

    date = Column(Date, primary_key=True, index=True)
    title_slug = Column(String(200), nullable=False)


class Group(Base):
    """Friend Group with unique invite code."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """Junction table for Group members."""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)


class Kudos(Base):
    """Thumbs up kudos sent between users with 24-hour expiration."""
    __tablename__ = "kudos"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_kudos_pair"),)



class PlatformActivity(Base):
    """Additional platform daily counts; legacy daily_activity remains LeetCode-only."""
    __tablename__ = "platform_activity"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    problems_solved = Column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("user_id", "platform", "date", name="uq_platform_activity"),)


class AdminOperation(Base):
    """Durable duplicate guard; contains no recipients, credentials, or message bodies."""
    __tablename__ = "admin_operations"
    operation_key = Column(String(120), primary_key=True)
    state = Column(String(20), nullable=False)
    started_at = Column(DateTime, nullable=False, default=utc_now)
    finished_at = Column(DateTime, nullable=True)


class AuthLimit(Base):
    """Fixed-window attempt counter keyed by HMAC, never raw email/IP/username."""
    __tablename__ = "auth_limits"
    bucket_key = Column(String(64), primary_key=True)
    window_started_at = Column(DateTime, nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0)


class AcceptedSubmission(Base):
    """Accepted-event evidence, separate from the one-question solve ledger."""
    __tablename__ = "accepted_submissions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    solve_id = Column(Integer, ForeignKey("solves.id", ondelete="CASCADE"), nullable=True, index=True)
    platform = Column(String(20), nullable=False)
    account_version = Column(Integer, nullable=False, default=0)
    submission_id = Column(String(80), nullable=False)
    title_slug = Column(String(200), nullable=False)
    accepted_at = Column(DateTime, nullable=False)
    observed_at = Column(DateTime, nullable=False, default=utc_now)
    evidence_kind = Column(String(30), nullable=False)
    first_solve_verified = Column(Boolean, nullable=False, default=False)
    __table_args__ = (
        UniqueConstraint("user_id", "platform", "account_version", "submission_id", name="uq_accepted_submission"),
        Index("ix_accepted_problem_time", "user_id", "platform", "account_version", "title_slug", "accepted_at"),
    )


class PointAward(Base):
    """Explicit base/daily/revision components with replay-safe award identities."""
    __tablename__ = "point_awards"
    id = Column(Integer, primary_key=True)
    award_key = Column(String(200), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    solve_id = Column(Integer, ForeignKey("solves.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("accepted_submissions.id", ondelete="SET NULL"), nullable=True, index=True)
    kind = Column(String(20), nullable=False)
    points = Column(Numeric(18, 4), nullable=False)
    earned_at = Column(DateTime, nullable=True)
    scoring_version = Column(String(40), nullable=False)
    input_snapshot = Column(JSON, nullable=False, default=dict)
    __table_args__ = (Index("ix_award_user_kind_time", "user_id", "kind", "earned_at"),)


class ScoreSnapshot(Base):
    """Private pre-reconciliation recovery evidence; never returned as a profile."""
    __tablename__ = "score_snapshots"
    id = Column(Integer, primary_key=True)
    snapshot_key = Column(String(200), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    captured_at = Column(DateTime, nullable=False, default=utc_now)
    reason = Column(String(40), nullable=False)
    payload = Column(JSON, nullable=False)


class AccountCredit(Base):
    """Explicit base-only estimates for questions missing from the unique ledger."""
    __tablename__ = "account_credits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    account_version = Column(Integer, nullable=False)
    kind = Column(String(30), nullable=False)
    points = Column(Numeric(18, 4), nullable=False)
    scoring_version = Column(String(40), nullable=False)
    input_snapshot = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "platform", "account_version", "kind", name="uq_account_credit"),)
