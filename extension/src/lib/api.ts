import { getStored } from "../storage";
export const API_BASE = "https://codestreak-api.onrender.com/api";

export interface RegisterResponse {
  id: number;
  name: string;
  leetcode_username: string;
  codeforces_username?: string;
  avatar_url?: string;
  access_token?: string;
  token_type?: string;
  created_at?: string;
  global_leaderboard_enabled?: boolean; // Deprecated display-only alias.
  show_global_leaderboard?: boolean;
}

export interface DayCount {
  date: string;
  problems_solved: number;
}

export interface PointBreakdown {
  difficulty?: string;
  raw_base_points?: number;
  ac_rate?: number;
  ac_multiplier?: number;
  ac_adjustment?: number;
  base_points: number;
  contest_rating?: number;
  is_daily: boolean;
  daily_bonus: number;
  subtotal?: number;
  streak_days: number;
  streak_multiplier: number;
  points_earned: number;
}

export interface RecentSolve {
  title_slug: string;
  title: string;
  solved_at: string;
  relative_time: string;
  leetcode_url: string;
  problem_url?: string;
  platform?: "leetcode" | "codeforces";
  source_handle?: string;
  source_submission_id?: number;
  problem_rating?: number;
  scoring_version?: string;
  points_earned?: number;
  breakdown?: PointBreakdown;
}

export interface DashboardResponse {
  leetcode_last_sync?: string;
  leetcode_history_state?: string;
  leetcode_history_gap?: boolean;
  leetcode_verified?: boolean;
  leetcode_verified_at?: string;
  codeforces_last_sync?: string;
  codeforces_sync_error?: string;
  codeforces_verified?: boolean;
  codeforces_verified_at?: string;
  codeforces_count?: number;
  codeforces_points?: number;
  leetcode_points?: number;
  points?: number;
  id: number;
  name: string;
  leetcode_username: string;
  codeforces_username?: string;
  avatar_url?: string;
  easy_count: number;
  medium_count: number;
  hard_count: number;
  current_streak: number;
  today_count: number;
  weekly_total: number;
  monthly_total: number;
  created_at?: string;
  last_7_days: DayCount[];
  global_leaderboard_enabled?: boolean; // Deprecated display-only alias.
  show_global_leaderboard?: boolean;
}

export interface BackendProgressResponse {
  user_id: number;
  followed: string[];
  hidden: string[];
  manual: string[];
  custom_plans: any[];
  version: number;
  updated_at?: string | null;
}

export interface InitiateVerificationResponse {
  platform: 'leetcode' | 'codeforces';
  handle: string;
  token: string;
  expires_at: string;
  instructions: string;
  is_claim_recovery: boolean;
}

export interface ConfirmVerificationResponse {
  status: string;
  platform: 'leetcode' | 'codeforces';
  handle: string;
  verified_at: string;
}

export interface PlatformVerificationStatus {
  handle: string | null;
  verified: boolean;
  verified_at: string | null;
  pending_token: boolean;
  expires_at: string | null;
}

export interface VerificationStatusResponse {
  user_id: number;
  leetcode: PlatformVerificationStatus;
  codeforces: PlatformVerificationStatus;
}


export interface LeaderboardEntry {
  codeforces_count?: number;
  codeforces_points?: number;
  leetcode_points?: number;
  leetcode_verified?: boolean;
  codeforces_verified?: boolean;
  rank: number;
  id: number;
  name: string;
  leetcode_username: string;
  codeforces_username?: string;
  avatar_url?: string;
  easy_count: number;
  medium_count: number;
  hard_count: number;
  points: number;
  weekly_total: number;
  current_streak: number;
  consistency_score: number;
  combined_score: number;
  is_active_today: boolean;
  kudos_count?: number;
  has_kudosed?: boolean;
}

export interface VersionCheckResponse {
  latest_version: string;
  min_supported_version: string;
  release_notes: string;
  download_url: string;
  crx_url: string;
}

export async function checkExtensionVersion(): Promise<VersionCheckResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/extension/version`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface DynamicMenuItem {
  id: string;
  label: string;
  icon: string;
  type: "tab" | "link" | "modal";
  url?: string;
  enabled: boolean;
}

export interface AppConfigResponse {
  version: string;
  maintenance_mode: boolean;
  announcement?: string;
  menu_items: DynamicMenuItem[];
  whatsapp_share_url?: string;
}

export async function getAppConfig(): Promise<AppConfigResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/config/app`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface LeaderboardResponse {
  week_start: string;
  week_end: string;
  total_users?: number;
  entries: LeaderboardEntry[];
}

export interface GroupMember {
  id: number;
  name: string;
  leetcode_username: string;
  codeforces_username?: string;
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

export const AUTH_EXPIRED = "leetstreak:auth-expired";

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); this.name = "ApiError"; }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = await getStored("codestreak_access_token");
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 401 && !path.startsWith("/users/login") && !path.startsWith("/users/register") && !path.startsWith("/users/forgot-password")) {
      if ((await getStored("codestreak_access_token")) === token) window.dispatchEvent(new Event(AUTH_EXPIRED));
    }
    const detail = typeof body.detail === "string" ? body.detail : Array.isArray(body.detail) ? body.detail.map((item: { msg?: string }) => item.msg || "Invalid input").join(". ") : `Request failed (${res.status})`;
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export const api = {
  register: (name: string, leetcode_username: string, email: string, password: string, show_global_leaderboard: boolean = true, codeforces_username?: string) =>
    request<RegisterResponse>("/users/register", {
      method: "POST",
      body: JSON.stringify({ name, leetcode_username, email, password, show_global_leaderboard, ...(codeforces_username?.trim() ? { codeforces_username: codeforces_username.trim() } : {}) }),
    }),
  login: (leetcode_username: string, password: string) =>
    request<RegisterResponse>("/users/login", {
      method: "POST",
      body: JSON.stringify({ leetcode_username, password }),
    }),
  initiateForgotPassword: (email_or_username: string) =>
    request<{ status: string; message: string }>("/users/forgot-password/initiate", {
      method: "POST",
      body: JSON.stringify({ email_or_username }),
    }),
  verifyForgotPassword: (email_or_username: string, otp: string, new_password: string) =>
    request<{ status: string }>("/users/forgot-password/verify", {
      method: "POST",
      body: JSON.stringify({ email_or_username, otp, new_password }),
    }),
  dashboard: (userId: number) =>
    request<DashboardResponse>(`/users/${userId}/dashboard`),
  syncUser: (userId: number) =>
    request<{ status: string; new_solves: number }>(`/users/${userId}/sync`, { method: "POST" }),
  updateLeetcodeUsername: (userId: number, leetcode_username: string) =>
    request<{ status: string; user_id: number; leetcode_username: string; avatar_url?: string }>(
      `/users/${userId}/leetcode-username`,
      {
        method: "PUT",
        body: JSON.stringify({ leetcode_username }),
      }
    ),
  updateCodeforcesUsername: (userId: number, codeforces_username: string) =>
    request<{ status: string; codeforces_username: string }>(`/users/${userId}/codeforces-username`, {
      method: "PUT", body: JSON.stringify({ codeforces_username }),
    }),
  updateSettings: (userId: number, settings: { show_global_leaderboard: boolean }) =>
    request<{ status: string; user_id: number; global_leaderboard_enabled: boolean }>(
      `/users/${userId}/settings`,
      {
        method: "PUT",
        body: JSON.stringify(settings),
      }
    ),
  changePassword: (userId: number, current_password: string, new_password: string) =>
    request<{ status: string; access_token: string }>(`/users/${userId}/change-password`, { method: "POST", body: JSON.stringify({ current_password, new_password }) }),
  revokeSessions: (userId: number) => request<{ status: string }>(`/users/${userId}/revoke-sessions`, { method: "POST" }),
  deleteAccount: (userId: number, password: string) =>
    request<{ status: string; message: string }>(`/users/${userId}/delete-account`, {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  leaderboard: (userId?: number, sortBy: "points" | "streak" = "points") => {
    const params = new URLSearchParams();
    if (userId) params.set("user_id", String(userId));
    if (sortBy) params.set("sort_by", sortBy);
    return request<LeaderboardResponse>(`/leaderboard?${params.toString()}`);
  },
  friendsLeaderboard: (userId: number, sortBy: "points" | "streak" = "points") => {
    const params = new URLSearchParams();
    params.set("user_id", String(userId));
    if (sortBy) params.set("sort_by", sortBy);
    return request<LeaderboardResponse>(`/friends/leaderboard?${params.toString()}`);
  },
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
  transferGroup: (groupId: number, new_owner_id: number) => request<{ status: string }>(`/groups/${groupId}/transfer`, { method: "POST", body: JSON.stringify({ new_owner_id }) }),
  removeMember: (groupId: number, memberUserId: number, requesterUserId: number) =>
    request<{ status: string }>(
      `/groups/${groupId}/members/${memberUserId}?requester_id=${requesterUserId}`,
      { method: "DELETE" }
    ),
  deleteGroup: (groupId: number, requesterUserId: number) =>
    request<{ status: string; group_id: number }>(
      `/groups/${groupId}?requester_id=${requesterUserId}`,
      { method: "DELETE" }
    ),
  myGroups: (userId: number) =>
    request<GroupListResponse>(`/groups/my-groups/${userId}`),
  groupLeaderboard: (groupId: number, userId?: number, sortBy: "points" | "streak" = "points") => {
    const params = new URLSearchParams();
    if (userId) params.set("user_id", String(userId));
    if (sortBy) params.set("sort_by", sortBy);
    return request<LeaderboardResponse>(`/groups/${groupId}/leaderboard?${params.toString()}`);
  },
  toggleKudos: (toUserId: number, fromUserId: number) =>
    request<{ status: string; to_user_id: number; kudos_count: number; has_kudosed: boolean }>(
      `/kudos/${toUserId}`,
      {
        method: "POST",
        body: JSON.stringify({ from_user_id: fromUserId }),
      }
    ),
  kudosAll: (fromUserId: number, targetUserIds: number[]) =>
    request<{ status: string; updated_count: number }>("/kudos/kudos-all", {
      method: "POST",
      body: JSON.stringify({ from_user_id: fromUserId, target_user_ids: targetUserIds }),
    }),
  codeforcesSolves: (userId: number) => request<{ handle: string | null; slugs: string[]; synced_at: string | null }>(`/users/${userId}/codeforces-solves`),
  recentSolves: (userId: number, limit = 10) =>
    request<RecentSolve[]>(`/users/${userId}/recent-solves?limit=${limit}`),
  pollNow: () => request<{ polled: Record<string, number> }>("/admin/poll-now", { method: "POST" }),
  checkExtensionVersion: checkExtensionVersion,
  getAppConfig: getAppConfig,
  getProgress: (userId: number) => request<BackendProgressResponse>(`/users/${userId}/progress`),
  updateProgress: (userId: number, payload: { followed?: string[]; hidden?: string[]; manual?: string[]; base_version?: number }) =>
    request<BackendProgressResponse>(`/users/${userId}/progress`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  saveCustomPlan: (userId: number, plan: any) =>
    request<any>(`/users/${userId}/plans`, {
      method: "POST",
      body: JSON.stringify(plan),
    }),
  deleteCustomPlan: (userId: number, slug: string) =>
    request<{ ok: boolean; slug: string }>(`/users/${userId}/plans/${slug}`, {
      method: "DELETE",
    }),
  restoreStarters: (userId: number) =>
    request<{ ok: boolean }>(`/users/${userId}/plans/restore-starters`, {
      method: "POST",
    }),
  initiateVerification: (userId: number, platform: 'leetcode' | 'codeforces', handle?: string) =>
    request<InitiateVerificationResponse>(`/users/${userId}/verify-handle/initiate`, {
      method: 'POST',
      body: JSON.stringify({ platform, handle }),
    }),
  confirmVerification: (userId: number, platform: 'leetcode' | 'codeforces') =>
    request<ConfirmVerificationResponse>(`/users/${userId}/verify-handle/confirm`, {
      method: 'POST',
      body: JSON.stringify({ platform }),
    }),
  verificationStatus: (userId: number) =>
    request<VerificationStatusResponse>(`/users/${userId}/verify-handle/status`),
};


export function showGlobalLeaderboard(profile?: { show_global_leaderboard?: boolean; global_leaderboard_enabled?: boolean } | null): boolean {
  return profile?.show_global_leaderboard ?? profile?.global_leaderboard_enabled ?? true;
}
