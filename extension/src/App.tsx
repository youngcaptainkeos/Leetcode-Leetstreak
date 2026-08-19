import { useEffect, useState } from "react";
import {
  api,
  DashboardResponse,
  LeaderboardResponse,
  LeaderboardEntry,
  GroupResponse,
} from "./lib/api";
import { getStored, setStored, clearStored } from "./storage";

type View = "loading" | "onboarding" | "dashboard";
type BoardTab = "global" | number; // "global" or groupId

export default function App() {
  const [view, setView] = useState<View>("loading");
  const [userId, setUserId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const stored = await getStored("codestreak_user_id");
      if (stored) {
        setUserId(Number(stored));
        setView("dashboard");
      } else {
        setView("onboarding");
      }
    })();
  }, []);

  async function handleRegistered(id: number) {
    await setStored("codestreak_user_id", String(id));
    setUserId(id);
    setView("dashboard");
  }

  async function handleLogout() {
    await clearStored(["codestreak_user_id"]);
    setUserId(null);
    setView("onboarding");
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo-group">
          <span className="logo-icon">🔥</span>
          <span className="logo-text">CodeStreak</span>
        </div>
        {view === "dashboard" && (
          <button className="link-btn" onClick={handleLogout}>
            Switch user
          </button>
        )}
      </header>

      {view === "loading" && <div className="centered muted">Loading profile…</div>}
      {view === "onboarding" && (
        <Onboarding onRegistered={handleRegistered} onError={setError} />
      )}
      {view === "dashboard" && userId && (
        <Dashboard userId={userId} onResetUser={handleLogout} />
      )}
      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}

function Onboarding({
  onRegistered,
  onError,
}: {
  onRegistered: (id: number) => void;
  onError: (e: string | null) => void;
}) {
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !username.trim()) return;
    setBusy(true);
    onError(null);
    try {
      const res = await api.register(name.trim(), username.trim());
      onRegistered(res.id);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="onboarding" onSubmit={submit}>
      <div className="onboarding-welcome">
        <h2>Welcome to CodeStreak</h2>
        <p className="muted small">
          Track LeetCode consistency with friends, form private groups, and build your daily streak.
        </p>
      </div>

      <label>
        <span>Your Name</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Alex"
          required
        />
      </label>

      <label>
        <span>LeetCode Username</span>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g. neal_wu"
          required
        />
      </label>

      <button type="submit" className="primary-btn" disabled={busy}>
        {busy ? "Connecting LeetCode…" : "Connect Profile"}
      </button>
      <p className="muted tiny text-center">
        Ensure your LeetCode profile is set to Public.
      </p>
    </form>
  );
}

function Dashboard({
  userId,
  onResetUser,
}: {
  userId: number;
  onResetUser: () => void;
}) {
  const [dash, setDash] = useState<DashboardResponse | null>(null);
  const [board, setBoard] = useState<LeaderboardResponse | null>(null);
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [selectedTab, setSelectedTab] = useState<BoardTab>("global");

  // Inspect Friend Stats Modal
  const [inspectedFriend, setInspectedFriend] = useState<LeaderboardEntry | null>(
    null
  );
  const [friendDash, setFriendDash] = useState<DashboardResponse | null>(null);
  const [loadingFriendDash, setLoadingFriendDash] = useState(false);

  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Group Modal States
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [groupActionBusy, setGroupActionBusy] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  async function loadData(tab: BoardTab = selectedTab) {
    try {
      const dashRes = await api.dashboard(userId).catch((err) => {
        if (err.message.includes("404") || err.message.includes("not found")) {
          onResetUser();
          return null;
        }
        throw err;
      });

      if (!dashRes) return;

      const myGroupsRes = await api.myGroups(userId);
      setDash(dashRes);
      setGroups(myGroupsRes.groups);

      // Load leaderboard based on tab
      let boardRes: LeaderboardResponse;
      if (tab === "global" || typeof tab !== "number") {
        boardRes = await api.leaderboard(userId);
      } else {
        boardRes = await api.groupLeaderboard(tab);
      }
      setBoard(boardRes);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't load dashboard.");
    }
  }

  useEffect(() => {
    loadData(selectedTab);
  }, [userId, selectedTab]);

  async function handleSync() {
    setSyncing(true);
    setSyncMsg(null);
    setError(null);
    try {
      const res = await api.syncUser(userId);
      await api.pollNow();
      await loadData();
      setSyncMsg(
        res.new_solves > 0
          ? `Synced! ${res.new_solves} new solve(s) added.`
          : "LeetCode up to date!"
      );
      setTimeout(() => setSyncMsg(null), 3500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  async function handleCreateGroup(e: React.FormEvent) {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    setGroupActionBusy(true);
    try {
      const group = await api.createGroup(userId, newGroupName.trim());
      setNewGroupName("");
      setShowCreateGroup(false);
      setSelectedTab(group.id);
      await loadData(group.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create group.");
    } finally {
      setGroupActionBusy(false);
    }
  }

  async function handleJoinGroup(e: React.FormEvent) {
    e.preventDefault();
    if (!joinCode.trim()) return;
    setGroupActionBusy(true);
    try {
      const group = await api.joinGroup(userId, joinCode.trim());
      setJoinCode("");
      setShowJoinGroup(false);
      setSelectedTab(group.id);
      await loadData(group.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to join group.");
    } finally {
      setGroupActionBusy(false);
    }
  }

  async function handleRemoveMember(
    groupId: number,
    memberUserId: number,
    memberName: string
  ) {
    if (!confirm(`Are you sure you want to remove ${memberName} from this group?`))
      return;
    try {
      await api.removeMember(groupId, memberUserId, userId);
      await loadData(groupId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove member.");
    }
  }

  async function handleInspectFriend(entry: LeaderboardEntry) {
    setInspectedFriend(entry);
    setLoadingFriendDash(true);
    try {
      const friendData = await api.dashboard(entry.id);
      setFriendDash(friendData);
    } catch (err) {
      console.warn("Could not load friend detailed dashboard", err);
    } finally {
      setLoadingFriendDash(false);
    }
  }

  function handleCopyCode(code: string) {
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  }

  if (error && !dash) return <div className="error-banner">{error}</div>;
  if (!dash || !board) return <div className="centered muted">Loading data…</div>;

  const maxDay = Math.max(1, ...dash.last_7_days.map((d) => d.problems_solved));
  const dayLabels = dash.last_7_days.map((d) =>
    new Date(d.date).toLocaleDateString(undefined, { weekday: "narrow" })
  );

  const activeGroup =
    selectedTab !== "global"
      ? groups.find((g) => g.id === selectedTab)
      : null;

  const isGroupOwner =
    activeGroup && activeGroup.creator_id === userId;

  return (
    <div className="dashboard">
      {/* Profile Bar */}
      <div className="profile-bar">
        <div className="profile-info">
          {dash.avatar_url ? (
            <img src={dash.avatar_url} alt={dash.name} className="avatar" />
          ) : (
            <div className="avatar-placeholder">{dash.name[0].toUpperCase()}</div>
          )}
          <div>
            <div className="profile-name">{dash.name}</div>
            <a
              href={`https://leetcode.com/${dash.leetcode_username}`}
              target="_blank"
              rel="noreferrer"
              className="profile-handle"
            >
              @{dash.leetcode_username}
            </a>
          </div>
        </div>

        <button
          className="sync-btn"
          onClick={handleSync}
          disabled={syncing}
          title="Force sync latest LeetCode activity"
        >
          {syncing ? "Syncing…" : "🔄 Sync"}
        </button>
      </div>

      {syncMsg && <div className="sync-banner">{syncMsg}</div>}
      {error && <div className="error-banner">{error}</div>}

      {/* Streak Hero Card */}
      <div className="streak-card">
        <div className="streak-hero">
          <span className="flame-icon">🔥</span>
          <span className="streak-count">{dash.current_streak}</span>
        </div>
        <div className="streak-label">DAY STREAK</div>
      </div>

      {/* Stats Breakdown */}
      <div className="stat-row">
        <Stat label="Today" value={dash.today_count} />
        <Stat label="This Week" value={dash.weekly_total} />
        <Stat label="This Month" value={dash.monthly_total} />
      </div>

      {/* Difficulty Counts */}
      <div className="diff-pills">
        <span className="diff-pill easy">Easy {dash.easy_count}</span>
        <span className="diff-pill medium">Med {dash.medium_count}</span>
        <span className="diff-pill hard">Hard {dash.hard_count}</span>
      </div>

      {/* 7-Day Activity Chart */}
      <div className="section">
        <div className="section-title">Last 7 Days Activity</div>
        <div className="heatmap">
          {dash.last_7_days.map((d, i) => (
            <div className="heat-col" key={d.date}>
              <div
                className="heat-bar"
                style={{
                  height: `${(d.problems_solved / maxDay) * 32 + 4}px`,
                  opacity: d.problems_solved > 0 ? 1 : 0.25,
                }}
                title={`${d.date}: ${d.problems_solved} solved`}
              />
              <span className="tiny muted">{dayLabels[i]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Groups & Leaderboard Navigation */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">Leaderboard</div>
          <div className="group-btn-group">
            <button
              className="chip-btn"
              onClick={() => setShowCreateGroup(!showCreateGroup)}
            >
              + Create Group
            </button>
            <button
              className="chip-btn"
              onClick={() => setShowJoinGroup(!showJoinGroup)}
            >
              Join Code
            </button>
          </div>
        </div>

        {/* Create Group Inline Form */}
        {showCreateGroup && (
          <form className="inline-form" onSubmit={handleCreateGroup}>
            <input
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="Group name (e.g. Code Bros)"
              autoFocus
            />
            <button type="submit" className="primary-btn sm" disabled={groupActionBusy}>
              {groupActionBusy ? "Creating…" : "Create"}
            </button>
          </form>
        )}

        {/* Join Group Inline Form */}
        {showJoinGroup && (
          <form className="inline-form" onSubmit={handleJoinGroup}>
            <input
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="Invite code (e.g. STREAK-X79)"
              autoFocus
            />
            <button type="submit" className="primary-btn sm" disabled={groupActionBusy}>
              {groupActionBusy ? "Joining…" : "Join"}
            </button>
          </form>
        )}

        {/* Board Switcher Tabs */}
        <div className="board-tabs">
          <button
            className={`tab-btn ${selectedTab === "global" ? "active" : ""}`}
            onClick={() => setSelectedTab("global")}
          >
            🌐 All Friends
          </button>
          {groups.map((g) => (
            <button
              key={g.id}
              className={`tab-btn ${selectedTab === g.id ? "active" : ""}`}
              onClick={() => setSelectedTab(g.id)}
            >
              👥 {g.name}
            </button>
          ))}
        </div>

        {/* Active Group Code & Owner Info Box */}
        {activeGroup && (
          <div className="group-invite-box">
            <div className="group-invite-info">
              <span className="muted tiny">Code:</span>
              <code className="invite-code">{activeGroup.code}</code>
              {isGroupOwner && <span className="owner-badge">👑 Owner</span>}
            </div>
            <button
              className="copy-btn"
              onClick={() => handleCopyCode(activeGroup.code)}
            >
              {copiedCode ? "Copied!" : "Copy Code"}
            </button>
          </div>
        )}

        {/* Leaderboard List */}
        <ul className="leaderboard">
          {board.entries.length === 0 ? (
            <li className="centered muted py-3">No members in this group yet.</li>
          ) : (
            board.entries.map((e) => (
              <li
                key={e.id}
                className={`leaderboard-item ${e.id === userId ? "me" : ""}`}
              >
                <div
                  className="clickable-user"
                  onClick={() => handleInspectFriend(e)}
                  title="Click to view detailed friend stats"
                >
                  <span className="rank">{e.rank}</span>
                  {e.avatar_url ? (
                    <img src={e.avatar_url} alt={e.name} className="rank-avatar" />
                  ) : (
                    <span className="rank-avatar-placeholder">{e.name[0]}</span>
                  )}
                  <div className="name-col">
                    <div className="name-row">
                      <span
                        className="dot"
                        style={{ opacity: e.is_active_today ? 1 : 0.25 }}
                        title={e.is_active_today ? "Solved today" : "Not solved today"}
                      >
                        ●
                      </span>
                      <span className="name">{e.name}</span>
                    </div>
                    <span className="handle-mini">@{e.leetcode_username}</span>
                  </div>
                  <span className="streak-mini">🔥{e.current_streak}</span>
                  <span className="score-badge">{e.weekly_total}</span>
                </div>

                {/* Owner Remove Button */}
                {isGroupOwner && e.id !== userId && activeGroup && (
                  <button
                    className="remove-btn"
                    onClick={(evt) => {
                      evt.stopPropagation();
                      handleRemoveMember(activeGroup.id, e.id, e.name);
                    }}
                    title={`Remove ${e.name} from group`}
                  >
                    🗑️
                  </button>
                )}
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Inspect Friend Modal */}
      {inspectedFriend && (
        <div className="modal-overlay" onClick={() => setInspectedFriend(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setInspectedFriend(null)}
            >
              ✕
            </button>
            <div className="modal-header">
              {inspectedFriend.avatar_url ? (
                <img
                  src={inspectedFriend.avatar_url}
                  alt={inspectedFriend.name}
                  className="modal-avatar"
                />
              ) : (
                <div className="avatar-placeholder lg">
                  {inspectedFriend.name[0]}
                </div>
              )}
              <div>
                <h3>{inspectedFriend.name}</h3>
                <a
                  href={`https://leetcode.com/${inspectedFriend.leetcode_username}`}
                  target="_blank"
                  rel="noreferrer"
                  className="profile-handle"
                >
                  @{inspectedFriend.leetcode_username} ↗
                </a>
              </div>
            </div>

            <div className="modal-streak-box">
              <span className="flame-icon">🔥</span>
              <span className="modal-streak-count">
                {inspectedFriend.current_streak} Day Streak
              </span>
            </div>

            <div className="stat-row">
              <Stat
                label="Today"
                value={
                  friendDash ? friendDash.today_count : (inspectedFriend.is_active_today ? 1 : 0)
                }
              />
              <Stat label="This Week" value={inspectedFriend.weekly_total} />
              <Stat
                label="This Month"
                value={friendDash ? friendDash.monthly_total : 0}
              />
            </div>

            <div className="diff-pills">
              <span className="diff-pill easy">
                Easy {inspectedFriend.easy_count}
              </span>
              <span className="diff-pill medium">
                Med {inspectedFriend.medium_count}
              </span>
              <span className="diff-pill hard">
                Hard {inspectedFriend.hard_count}
              </span>
            </div>

            {loadingFriendDash ? (
              <div className="centered muted tiny">Loading recent activity…</div>
            ) : friendDash ? (
              <div className="section">
                <div className="section-title">7-Day Activity</div>
                <div className="heatmap">
                  {friendDash.last_7_days.map((d, i) => (
                    <div className="heat-col" key={d.date}>
                      <div
                        className="heat-bar"
                        style={{
                          height: `${
                            (d.problems_solved /
                              Math.max(
                                1,
                                ...friendDash.last_7_days.map((x) => x.problems_solved)
                              )) *
                              32 +
                            4
                          }px`,
                          opacity: d.problems_solved > 0 ? 1 : 0.25,
                        }}
                        title={`${d.date}: ${d.problems_solved} solved`}
                      />
                      <span className="tiny muted">{dayLabels[i]}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="tiny muted">{label}</div>
    </div>
  );
}


