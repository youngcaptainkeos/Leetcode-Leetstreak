from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RecentSolveSchema(BaseModel):
    title_slug: str
    title: str
    solved_at: datetime
    relative_time: str
    leetcode_url: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    leetcode_username: str = Field(min_length=1, max_length=80)


class RegisterResponse(BaseModel):
    id: int
    name: str
    leetcode_username: str
    avatar_url: Optional[str] = None


class DayCount(BaseModel):
    date: date
    problems_solved: int


class DashboardResponse(BaseModel):
    id: int
    name: str
    leetcode_username: str
    avatar_url: Optional[str] = None
    easy_count: int = 0
    medium_count: int = 0
    hard_count: int = 0
    current_streak: int
    today_count: int
    weekly_total: int
    monthly_total: int
    last_7_days: List[DayCount]


class LeaderboardEntry(BaseModel):
    rank: int
    id: int
    name: str
    leetcode_username: str
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


class LeaderboardResponse(BaseModel):
    week_start: date
    week_end: date
    entries: List[LeaderboardEntry]


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    user_id: int


class GroupJoinRequest(BaseModel):
    code: str = Field(min_length=4, max_length=20)
    user_id: int


class GroupMemberSchema(BaseModel):
    id: int
    name: str
    leetcode_username: str
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

