from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PointBreakdownSchema(BaseModel):
    difficulty: Optional[str] = "Medium"
    raw_base_points: float = 0.0
    ac_rate: Optional[float] = None
    ac_multiplier: float = 1.0
    ac_adjustment: float = 0.0
    base_points: float = 0.0
    contest_rating: Optional[float] = None
    is_daily: bool = False
    daily_bonus: float = 0.0
    subtotal: float = 0.0
    streak_days: int = 0
    streak_multiplier: float = 1.0
    points_earned: float = 0


class RecentSolveSchema(BaseModel):
    title_slug: str
    title: str
    solved_at: datetime
    relative_time: str
    leetcode_url: str  # Legacy alias; points to the actual platform URL.
    problem_url: Optional[str] = None
    platform: str = "leetcode"
    source_handle: Optional[str] = None
    source_submission_id: Optional[int] = None
    problem_rating: Optional[float] = None
    scoring_version: str = "leetcode-v1"
    points_earned: float = 0
    breakdown: Optional[PointBreakdownSchema] = None


class RegisterRequest(BaseModel):
    codeforces_username: Optional[str] = Field(default=None, max_length=24)
    name: str = Field(min_length=1, max_length=80)
    leetcode_username: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=4, max_length=100)
    global_leaderboard_enabled: bool = True


class LoginRequest(BaseModel):
    leetcode_username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=100)


class ForgotPasswordInitiateRequest(BaseModel):
    email_or_username: str = Field(min_length=1, max_length=120)


class ForgotPasswordVerifyRequest(BaseModel):
    email_or_username: str = Field(min_length=1, max_length=120)
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=4, max_length=100)


class UpdateUsernameRequest(BaseModel):
    leetcode_username: str = Field(min_length=1, max_length=80)


class UpdateCodeforcesRequest(BaseModel):
    codeforces_username: str = Field(min_length=3, max_length=24)


class UpdateSettingsRequest(BaseModel):
    global_leaderboard_enabled: bool


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class RegisterResponse(BaseModel):
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
    created_at: Optional[datetime] = None
    global_leaderboard_enabled: bool = True


class DayCount(BaseModel):
    date: date
    problems_solved: int


class DashboardResponse(BaseModel):
    codeforces_last_sync: Optional[datetime] = None
    codeforces_sync_error: Optional[str] = None
    codeforces_count: int = 0
    codeforces_points: float = 0
    leetcode_points: float = 0
    points: float = 0
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None
    easy_count: int = 0
    medium_count: int = 0
    hard_count: int = 0
    current_streak: int
    today_count: int
    weekly_total: int
    monthly_total: int
    created_at: Optional[datetime] = None
    last_7_days: List[DayCount]
    global_leaderboard_enabled: bool = True


class LeaderboardEntry(BaseModel):
    codeforces_count: int = 0
    codeforces_points: float = 0
    leetcode_points: float = 0
    rank: int
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None
    easy_count: int = 0
    medium_count: int = 0
    hard_count: int = 0
    points: int = 0
    weekly_total: int
    current_streak: int
    consistency_score: float  # 0-100, active days / 7
    combined_score: float     # 0-100, 0.6*consistency + 0.4*normalized volume
    is_active_today: bool
    kudos_count: int = 0
    has_kudosed: bool = False


class KudosToggleRequest(BaseModel):
    from_user_id: int


class KudosAllRequest(BaseModel):
    from_user_id: int
    target_user_ids: List[int] = Field(default_factory=list)


class LeaderboardResponse(BaseModel):
    week_start: date
    week_end: date
    total_users: int = 0
    entries: List[LeaderboardEntry]


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    user_id: int


class GroupJoinRequest(BaseModel):
    code: str = Field(min_length=4, max_length=20)
    user_id: int


class GroupTransferRequest(BaseModel):
    new_owner_id: int = Field(gt=0)


class ReleaseBroadcastRequest(BaseModel):
    model_config = {"extra": "forbid"}
    release_id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9-]+$")
    dry_run: bool = True


class GroupMemberSchema(BaseModel):
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    code: str
    creator_id: Optional[int] = None
    member_count: int
    members: List[GroupMemberSchema]


class GroupListResponse(BaseModel):
    groups: List[GroupResponse]


class ActivityFeedItemSchema(BaseModel):
    user_id: int
    user_name: str
    user_handle: str
    title: str
    title_slug: str
    solved_at: datetime
    relative_time: str
    leetcode_url: str  # Legacy alias; points to the actual platform URL.
    problem_url: Optional[str] = None
    platform: str = "leetcode"
    source_handle: Optional[str] = None
    source_submission_id: Optional[int] = None
    problem_rating: Optional[float] = None
    scoring_version: str = "leetcode-v1"


class DynamicMenuItem(BaseModel):
    id: str
    label: str
    icon: str
    type: str  # "tab", "link", "modal"
    url: Optional[str] = None
    enabled: bool = True


class AppConfigResponse(BaseModel):
    version: str
    maintenance_mode: bool = False
    announcement: Optional[str] = None
    menu_items: List[DynamicMenuItem]
    whatsapp_share_url: Optional[str] = None
class SyncRequest(BaseModel):
    attempts_map: Optional[Dict[str, dict]] = None

