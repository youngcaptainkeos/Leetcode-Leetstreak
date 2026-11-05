from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import re


def validate_new_password(value: str) -> str:
    if len(value) < 15 or len(value) > 100:
        raise ValueError("Use a password or passphrase with 15 to 100 characters.")
    if value.lower() in {"123456789012345", "passwordpassword", "qwertyqwertyqwerty"}:
        raise ValueError("Choose a less common password or passphrase.")
    return value


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
    password: str = Field(min_length=15, max_length=100)
    global_leaderboard_enabled: bool = True
    show_global_leaderboard: Optional[bool] = None

    _password_policy = field_validator("password")(validate_new_password)

    @model_validator(mode="after")
    def consistent_display_choice(self):
        if "global_leaderboard_enabled" in self.model_fields_set and self.show_global_leaderboard is not None and self.global_leaderboard_enabled != self.show_global_leaderboard:
            raise ValueError("Conflicting Global display preferences.")
        return self

    @field_validator("email")
    @classmethod
    def email_format(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    leetcode_username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=100)


class ForgotPasswordInitiateRequest(BaseModel):
    email_or_username: str = Field(min_length=1, max_length=120)


class ForgotPasswordVerifyRequest(BaseModel):
    email_or_username: str = Field(min_length=1, max_length=120)
    otp: str = Field(pattern=r"^[0-9]{6}$")
    new_password: str = Field(min_length=15, max_length=100)
    _password_policy = field_validator("new_password")(validate_new_password)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=15, max_length=100)
    _password_policy = field_validator("new_password")(validate_new_password)


class UpdateUsernameRequest(BaseModel):
    leetcode_username: str = Field(min_length=1, max_length=80)


class UpdateCodeforcesRequest(BaseModel):
    codeforces_username: str = Field(min_length=3, max_length=24)


class UpdateSettingsRequest(BaseModel):
    global_leaderboard_enabled: Optional[bool] = Field(default=None, deprecated=True)
    show_global_leaderboard: Optional[bool] = None

    @model_validator(mode="after")
    def consistent_display_choice(self):
        if self.show_global_leaderboard is None and self.global_leaderboard_enabled is None:
            raise ValueError("Choose whether to show the Global leaderboard.")
        if self.show_global_leaderboard is not None and self.global_leaderboard_enabled is not None and self.show_global_leaderboard != self.global_leaderboard_enabled:
            raise ValueError("Conflicting Global display preferences.")
        return self


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
    show_global_leaderboard: bool = True
    leetcode_verified: bool = False
    codeforces_verified: bool = False


class DayCount(BaseModel):
    date: date
    problems_solved: int


class DashboardResponse(BaseModel):
    leetcode_last_sync: Optional[datetime] = None
    leetcode_history_state: Optional[str] = "partial"
    leetcode_history_gap: Optional[bool] = True
    leetcode_verified: bool = False
    leetcode_verified_at: Optional[datetime] = None
    codeforces_last_sync: Optional[datetime] = None
    codeforces_sync_error: Optional[str] = None
    codeforces_verified: bool = False
    codeforces_verified_at: Optional[datetime] = None
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
    global_leaderboard_enabled: Optional[bool] = None
    show_global_leaderboard: Optional[bool] = None


class LeaderboardEntry(BaseModel):
    codeforces_count: int = 0
    codeforces_points: float = 0
    leetcode_points: float = 0
    leetcode_verified: bool = False
    codeforces_verified: bool = False
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
    period: str = "all"
    period_start: Optional[date] = None
    period_end: Optional[date] = None



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
    leetcode_verified: bool = False
    codeforces_verified: bool = False


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


class StudyQuestionSchema(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    titleSlug: str = Field(min_length=1, max_length=200)
    difficulty: str = Field(default="MEDIUM", max_length=20)
    url: Optional[str] = Field(default=None, max_length=1000)
    leetcodeSlug: Optional[str] = Field(default=None, max_length=200)
    kind: Optional[str] = Field(default=None, max_length=20)


class StudyPlanSubGroupSchema(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    questions: List[StudyQuestionSchema] = Field(default_factory=list)


class StudyPlanPayload(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=100)
    planSubGroups: List[StudyPlanSubGroupSchema] = Field(default_factory=list)
    source: Optional[str] = Field(default="external", max_length=40)
    sourceUrl: Optional[str] = Field(default=None, max_length=1000)
    snapshotDate: Optional[str] = Field(default=None, max_length=20)


class ProgressUpdateRequest(BaseModel):
    followed: Optional[List[str]] = None
    hidden: Optional[List[str]] = None
    manual: Optional[List[str]] = None
    base_version: Optional[int] = None


class ProgressResponse(BaseModel):
    user_id: int
    followed: List[str]
    hidden: List[str]
    manual: List[str]
    custom_plans: List[dict]
    version: int
    updated_at: Optional[str] = None


class InitiateVerificationRequest(BaseModel):
    platform: str = Field(pattern=r"^(leetcode|codeforces)$")
    handle: Optional[str] = None


class InitiateVerificationResponse(BaseModel):
    platform: str
    handle: str
    token: str
    expires_at: datetime
    instructions: str
    is_claim_recovery: bool = False


class ConfirmVerificationRequest(BaseModel):
    platform: str = Field(pattern=r"^(leetcode|codeforces)$")
    handle: Optional[str] = None


class ConfirmVerificationResponse(BaseModel):
    status: str = "verified"
    platform: str
    handle: str
    verified_at: datetime


class PlatformVerificationStatus(BaseModel):
    handle: Optional[str] = None
    verified: bool = False
    verified_at: Optional[datetime] = None
    pending_token: bool = False
    expires_at: Optional[datetime] = None


class VerificationStatusResponse(BaseModel):
    user_id: int
    leetcode: PlatformVerificationStatus
    codeforces: PlatformVerificationStatus


class UnlinkCodeforcesResponse(BaseModel):
    status: str = "unlinked"
    message: str
    points: float


class FriendSummary(BaseModel):
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None
    leetcode_verified: bool = False
    codeforces_verified: bool = False
    points: Optional[float] = None
    current_streak: Optional[int] = None


class FriendRequestItem(BaseModel):
    id: int
    user: FriendSummary
    created_at: datetime


class FriendsListResponse(BaseModel):
    friends: List[FriendSummary]
    incoming_requests: List[FriendRequestItem]
    outgoing_requests: List[FriendRequestItem]


class SendFriendRequest(BaseModel):
    target: str = Field(min_length=1, max_length=100)


class UserSearchResult(BaseModel):
    id: int
    name: str
    leetcode_username: str
    codeforces_username: Optional[str] = None
    avatar_url: Optional[str] = None
    leetcode_verified: bool = False
    codeforces_verified: bool = False
    friendship_status: Optional[str] = None


class FriendshipActionResponse(BaseModel):
    status: str
    message: str


# --- FEAT-08: History, Activity Views, and Exports ---

class SolveHistoryItemSchema(BaseModel):
    id: int
    platform: str
    title_slug: str
    title: str
    difficulty: Optional[str] = None
    problem_rating: Optional[float] = None
    solved_at: datetime
    points_earned: float = 0.0
    is_daily: bool = False
    scoring_version: str = "leetcode-v1"
    problem_url: Optional[str] = None


class SolveHistoryCoverageSchema(BaseModel):
    oldest_solve_at: Optional[datetime] = None
    newest_solve_at: Optional[datetime] = None
    total_solves: int = 0
    leetcode_solves: int = 0
    codeforces_solves: int = 0
    leetcode_username: Optional[str] = None
    leetcode_verified: bool = False
    codeforces_username: Optional[str] = None
    codeforces_verified: bool = False
    history_complete: bool = False


class SolveHistoryResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    coverage: SolveHistoryCoverageSchema
    solves: List[SolveHistoryItemSchema]


class ActivityHeatmapDaySchema(BaseModel):
    date: date
    status: str  # "active", "zero", "unobserved"
    count: int
    points: float
    platforms: List[str] = Field(default_factory=list)


class ActivityHeatmapResponse(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    total_days: int
    active_days: int
    zero_days: int
    unobserved_days: int
    days: List[ActivityHeatmapDaySchema]


class PlanExportResponse(BaseModel):
    version: int = 1
    exported_at: datetime
    user_id: int
    followed_plans: List[str] = Field(default_factory=list)
    hidden_plans: List[str] = Field(default_factory=list)
    manual_solves: List[str] = Field(default_factory=list)
    custom_plans: List[dict] = Field(default_factory=list)


class PlanImportPayload(BaseModel):
    version: int = 1
    followed_plans: Optional[List[str]] = None
    hidden_plans: Optional[List[str]] = None
    manual_solves: Optional[List[str]] = None
    custom_plans: Optional[List[StudyPlanPayload]] = None


class PlanImportResponse(BaseModel):
    dry_run: bool
    mode: str
    plans_imported: int
    manual_solves_imported: int
    conflicts_resolved: int
    total_custom_plans: int
    message: str



