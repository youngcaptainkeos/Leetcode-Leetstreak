export const API_BASE = import.meta.env.VITE_API_BASE || "https://codestreak-api.onrender.com/api";

export interface RegisterResponse {
  id: number;
  name: string;
  leetcode_username: string;
  avatar_url?: string;
}

export interface DayCount {
  date: string;
  problems_solved: number;
}

export interface DashboardResponse {
  id: number;
  name: string;
  leetcode_username: string;
  avatar_url?: string;
  easy_count: number;
  medium_count: number;
  hard_count: number;
  current_streak: number;
  today_count: number;
  weekly_total: number;
  monthly_total: number;
  last_7_days: DayCount[];
}

export interface LeaderboardEntry {
  rank: number;
  id: number;
  name: string;
  leetcode_username: string;
  avatar_url?: string;
  easy_count: number;
  medium_count: number;
  hard_count: number;
  weekly_total: number;
  current_streak: number;
  consistency_score: number;
  combined_score: number;
  is_active_today: boolean;
}

export interface LeaderboardResponse {
  week_start: string;
  week_end: string;
  entries: LeaderboardEntry[];
}

export interface GroupMember {
  id: number;
  name: string;
  leetcode_username: string;
  avatar_url?: string;
}

export interface GroupResponse {
  id: number;
  name: string;
  code: string;
  creator_id?: number;
  member_count: number;
  members: GroupMember[];
}

export interface GroupListResponse {
  groups: GroupResponse[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  register: (name: string, leetcode_username: string) =>
    request<RegisterResponse>("/users/register", {
      method: "POST",
      body: JSON.stringify({ name, leetcode_username }),
    }),
  dashboard: (userId: number) =>
    request<DashboardResponse>(`/users/${userId}/dashboard`),
  syncUser: (userId: number) =>
    request<{ status: string; new_solves: number }>(`/users/${userId}/sync`, { method: "POST" }),
  leaderboard: (userId?: number) =>
    request<LeaderboardResponse>(userId ? `/leaderboard?user_id=${userId}` : "/leaderboard"),
  createGroup: (userId: number, name: string) =>
    request<GroupResponse>("/groups", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, name }),
    }),
  joinGroup: (userId: number, code: string) =>
    request<GroupResponse>("/groups/join", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, code }),
    }),
  removeMember: (groupId: number, memberUserId: number, requesterUserId: number) =>
    request<{ status: string }>(
      `/groups/${groupId}/members/${memberUserId}?requester_id=${requesterUserId}`,
      { method: "DELETE" }
    ),
  myGroups: (userId: number) =>
    request<GroupListResponse>(`/groups/my-groups/${userId}`),
  groupLeaderboard: (groupId: number) =>
    request<LeaderboardResponse>(`/groups/${groupId}/leaderboard`),
  pollNow: () => request<{ polled: Record<string, number> }>("/admin/poll-now", { method: "POST" }),
};

