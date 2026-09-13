import React, { useEffect, useState } from "react";
import {
  api,
  API_BASE,
  DashboardResponse,
  LeaderboardResponse,
  LeaderboardEntry,
  GroupResponse,
  RecentSolve,
  VersionCheckResponse,
  AppConfigResponse,
  DynamicMenuItem,
  checkExtensionVersion,
} from "./lib/api";
import { getStored, setStored, clearStored } from "./storage";

type View = "loading" | "onboarding" | "dashboard";
type BoardTab = "global" | "friends" | number; // "global", "friends", or groupId

export default function App() {
  const [view, setView] = useState<View>("loading");
  const [userId, setUserId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPointsHelp, setShowPointsHelp] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<VersionCheckResponse | null>(null);

  const [appConfig, setAppConfig] = useState<AppConfigResponse | null>(null);

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

  useEffect(() => {
    (async () => {
      try {
        const cfg = await api.getAppConfig();
        if (cfg) setAppConfig(cfg);
      } catch (err) {
        console.warn("App config fetch error:", err);
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const info = await checkExtensionVersion();
        if (info && info.latest_version) {
          const currentVer =
            (typeof chrome !== "undefined" && chrome.runtime?.getManifest?.()?.version) ||
            "1.0.0";
          const cParts = currentVer.split(".").map(Number);
          const lParts = info.latest_version.split(".").map(Number);
          let isNewer = false;
          for (let i = 0; i < Math.max(cParts.length, lParts.length); i++) {
            const c = cParts[i] || 0;
            const l = lParts[i] || 0;
            if (l > c) {
              isNewer = true;
              break;
            }
            if (l < c) {
              isNewer = false;
              break;
            }
          }
          if (isNewer) {
            setUpdateInfo(info);
          }
        }
      } catch (err) {
        console.warn("Update check error:", err);
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
          <img src="/icon48.png" alt="LeetStreak" className="header-logo-img" />
          <span className="logo-text">LeetStreak</span>
        </div>
        {view === "dashboard" && (
          <div className="header-actions">
            <a
              href={
                appConfig?.whatsapp_share_url ||
                "https://api.whatsapp.com/send?text=" +
                  encodeURIComponent(
                    "Check out LeetStreak to track your LeetCode daily streak and compete on leaderboards with friends! 🔥\n\nDownload Latest Extension: https://codestreak-api.onrender.com/downloads/leetstreak.zip\n\nSetup Guide: https://github.com/youngcaptainkeos/Leetcode-Leetstreak#readme"
                  )
              }
              target="_blank"
              rel="noopener noreferrer"
              className="whatsapp-icon-btn"
              title="Share LeetStreak on WhatsApp"
            >
              <svg className="whatsapp-icon-svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
            </a>
            <button
              className="help-btn"
              onClick={() => setShowPointsHelp(true)}
              title="How Points Work ❓"
            >
              ❓ Help
            </button>
          </div>
        )}
      </header>

      {updateInfo && (
        <div className="update-ota-banner">
          <div>
            🚀 <strong>Update v{updateInfo.latest_version} Available!</strong>
            <div style={{ fontSize: "10px", opacity: 0.85, marginTop: "2px" }}>
              {updateInfo.release_notes || "Performance fixes and new features available."}
            </div>
          </div>
          <a
            href={updateInfo.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="update-ota-btn"
          >
            Update Now
          </a>
        </div>
      )}

      {showPointsHelp && <PointsHelpModal onClose={() => setShowPointsHelp(false)} />}

      {view === "loading" && <div className="centered muted">Loading profile…</div>}
      {view === "onboarding" && (
        <Onboarding onRegistered={handleRegistered} onError={setError} />
      )}
      {view === "dashboard" && userId && (
        <Dashboard userId={userId} onResetUser={handleLogout} appConfigProp={appConfig} />
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
  const [authMode, setAuthMode] = useState<"login" | "register" | "forgot">("login");
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [forgotStep, setForgotStep] = useState<1 | 2>(1);
  const [sentEmail, setSentEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [draftsLoaded, setDraftsLoaded] = useState(false);

  const AUTH_STORAGE_KEYS = [
    "codestreak_auth_mode",
    "codestreak_forgot_step",
    "codestreak_sent_email",
    "codestreak_draft_name",
    "codestreak_draft_username",
    "codestreak_draft_email",
    "codestreak_draft_password",
    "codestreak_draft_new_password",
    "codestreak_draft_otp",
  ];

  useEffect(() => {
    (async () => {
      const storedMode = await getStored("codestreak_auth_mode");
      const storedStep = await getStored("codestreak_forgot_step");
      const storedEmail = await getStored("codestreak_sent_email");

      const draftName = await getStored("codestreak_draft_name");
      const draftUsername = await getStored("codestreak_draft_username");
      const draftEmail = await getStored("codestreak_draft_email");
      const draftPassword = await getStored("codestreak_draft_password");
      const draftNewPassword = await getStored("codestreak_draft_new_password");
      const draftOtp = await getStored("codestreak_draft_otp");

      if (draftName) setName(draftName);
      if (draftUsername) setUsername(draftUsername);
      if (draftEmail) setEmail(draftEmail);
      if (draftPassword) setPassword(draftPassword);
      if (draftNewPassword) setNewPassword(draftNewPassword);
      if (draftOtp) setOtp(draftOtp);

      if (storedMode === "forgot" && storedStep === "2" && storedEmail) {
        setAuthMode("forgot");
        setForgotStep(2);
        setSentEmail(storedEmail);
        if (!draftUsername) setUsername(storedEmail);
      } else if (storedMode === "login" || storedMode === "register" || storedMode === "forgot") {
        setAuthMode(storedMode as any);
      }
      setDraftsLoaded(true);
    })();
  }, []);

  // Save input drafts automatically as the user types
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_name", name); }, [name, draftsLoaded]);
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_username", username); }, [username, draftsLoaded]);
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_email", email); }, [email, draftsLoaded]);
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_password", password); }, [password, draftsLoaded]);
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_new_password", newPassword); }, [newPassword, draftsLoaded]);
  useEffect(() => { if (draftsLoaded) setStored("codestreak_draft_otp", otp); }, [otp, draftsLoaded]);

  const switchAuthMode = async (mode: "login" | "register" | "forgot") => {
    setAuthMode(mode);
    onError(null);
    setSuccessMsg(null);
    await setStored("codestreak_auth_mode", mode);
  };

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setBusy(true);
    onError(null);
    try {
      const res = await api.login(username.trim(), password);
      await clearStored(AUTH_STORAGE_KEYS);
      onRegistered(res.id);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !username.trim() || !email.trim() || !password) return;
    setBusy(true);
    onError(null);
    try {
      const res = await api.register(name.trim(), username.trim(), email.trim(), password);
      await clearStored(AUTH_STORAGE_KEYS);
      onRegistered(res.id);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleForgotInitiate(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim()) return;
    setBusy(true);
    onError(null);
    try {
      const res = await api.initiateForgotPassword(username.trim());
      setSentEmail(res.email);
      setForgotStep(2);
      setSuccessMsg(`Sent 6-digit code to ${res.email}`);
      await setStored("codestreak_auth_mode", "forgot");
      await setStored("codestreak_forgot_step", "2");
      await setStored("codestreak_sent_email", res.email);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not send reset code.");
    } finally {
      setBusy(false);
    }
  }

  async function handleForgotVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !otp.trim() || !newPassword) return;
    setBusy(true);
    onError(null);
    try {
      await api.verifyForgotPassword(username.trim(), otp.trim(), newPassword);
      setPassword(newPassword);
      const res = await api.login(username.trim(), newPassword);
      await clearStored(AUTH_STORAGE_KEYS);
      onRegistered(res.id);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="onboarding">
      <div className="onboarding-welcome">
        <h2>Welcome to LeetStreak</h2>
        <p className="muted small">
          Track LeetCode consistency with friends, form private groups, and build your daily streak.
        </p>
      </div>

      {successMsg && <div className="sync-banner">{successMsg}</div>}

      {/* Auth Card Container */}
      <div className="auth-card">
        {authMode !== "forgot" && (
          <div className="auth-tab-bar">
            <button
              type="button"
              className={`auth-tab-btn ${authMode === "login" ? "active" : ""}`}
              onClick={() => switchAuthMode("login")}
            >
              Log In
            </button>
            <button
              type="button"
              className={`auth-tab-btn ${authMode === "register" ? "active" : ""}`}
              onClick={() => switchAuthMode("register")}
            >
              Sign Up
            </button>
          </div>
        )}

        {authMode === "login" && (
          <form onSubmit={handleLogin} className="auth-form">
            <label>
              <span>Email</span>
              <input
                type="email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. alex@example.com"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </label>

            <button type="submit" className="primary-btn" disabled={busy}>
              {busy ? "Verifying…" : "Log In"}
            </button>

            <div className="auth-footer-links">
              <button
                type="button"
                className="link-btn tiny"
                onClick={() => { switchAuthMode("forgot"); setForgotStep(1); }}
              >
                Forgot Password?
              </button>
            </div>
          </form>
        )}

        {authMode === "register" && (
          <form onSubmit={handleRegister} className="auth-form">
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

            <label>
              <span>Email Address</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@example.com"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 4 characters"
                required
              />
            </label>

            <button type="submit" className="primary-btn" disabled={busy}>
              {busy ? "Creating Account…" : "Create Account"}
            </button>
          </form>
        )}

        {authMode === "forgot" && (
          <div className="auth-form">
            {forgotStep === 1 ? (
              <form onSubmit={handleForgotInitiate} className="auth-form">
                <p className="tiny muted mb-1">
                  Enter your Email address to receive a 6-digit reset code.
                </p>
                <label>
                  <span>Email Address</span>
                  <input
                    type="email"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. alex@example.com"
                    required
                  />
                </label>

                <button type="submit" className="primary-btn" disabled={busy}>
                  {busy ? "Sending Code…" : "Send Reset Code"}
                </button>

                <div className="auth-footer-links">
                  <button
                    type="button"
                    className="link-btn tiny"
                    onClick={() => switchAuthMode("login")}
                  >
                    ← Back to Log In
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleForgotVerify} className="auth-form">
                <p className="tiny muted mb-1">
                  Enter the 6-digit code sent to <strong>{sentEmail}</strong> and your new password.
                </p>

                <label>
                  <span>6-Digit Verification Code</span>
                  <input
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="e.g. 839102"
                    maxLength={6}
                    required
                  />
                </label>

                <label>
                  <span>New Password</span>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="New password"
                    required
                  />
                </label>

                <button type="submit" className="primary-btn" disabled={busy}>
                  {busy ? "Resetting…" : "Reset & Log In"}
                </button>

                <div className="auth-footer-links" style={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                  <button
                    type="button"
                    className="link-btn tiny"
                    onClick={() => switchAuthMode("login")}
                  >
                    ← Back to Log In
                  </button>
                  <button
                    type="button"
                    className="link-btn tiny"
                    onClick={() => setForgotStep(1)}
                  >
                    Resend Code
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface ActivityFeedItem {
  user_id: number;
  user_name: string;
  user_handle: string;
  title: string;
  title_slug: string;
  solved_at: string;
  relative_time: string;
  leetcode_url: string;
}

function Dashboard({
  userId,
  onResetUser,
  appConfigProp,
}: {
  userId: number;
  onResetUser: () => void;
  appConfigProp?: AppConfigResponse | null;
}) {
  const [dash, setDash] = useState<DashboardResponse | null>(null);
  const [board, setBoard] = useState<LeaderboardResponse | null>(null);
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [selectedTab, setSelectedTab] = useState<BoardTab>("global");
  const [sortBy, setSortBy] = useState<"points" | "streak">("points");
  const [revealedCodes, setRevealedCodes] = useState<Record<number, boolean>>({});
  const [activityFeed, setActivityFeed] = useState<ActivityFeedItem[]>([]);
  const [tabBoards, setTabBoards] = useState<Record<string, LeaderboardResponse>>({});
  const [boardLoading, setBoardLoading] = useState<boolean>(false);

  const changeTab = (tab: BoardTab) => {
    const tabKey = String(tab);
    setSelectedTab(tab);
    setStored("codestreak_active_tab", tabKey);

    // ⚡ INSTANT SWAP (0ms): Clear old board immediately if not cached so old users vanish at once!
    if (tabBoards[tabKey]) {
      setBoard(tabBoards[tabKey]);
      setBoardLoading(false);
    } else {
      setBoard(null);
      setBoardLoading(true);
    }
  };

  useEffect(() => {
    (async () => {
      const storedTab = await getStored("codestreak_active_tab");
      let activeTabKey = "global";
      if (storedTab) {
        if (storedTab === "global" || storedTab === "friends") {
          setSelectedTab(storedTab);
          activeTabKey = storedTab;
        } else if (!isNaN(Number(storedTab))) {
          setSelectedTab(Number(storedTab));
          activeTabKey = storedTab;
        }
      }
      // Instant 0ms stale-while-revalidate cached rendering
      const cachedDash = await getStored("codestreak_cached_dash");
      const cachedBoard = await getStored(`codestreak_cached_board_${activeTabKey}`) || await getStored("codestreak_cached_board");
      if (cachedDash) {
        try { setDash(JSON.parse(cachedDash)); } catch (e) {}
      }
      if (cachedBoard) {
        try {
          const parsed = JSON.parse(cachedBoard);
          setBoard(parsed);
          setTabBoards((prev) => ({ ...prev, [activeTabKey]: parsed }));
        } catch (e) {}
      }
    })();
  }, []);

  // Inspect Friend Stats Modal
  const [inspectedFriend, setInspectedFriend] = useState<LeaderboardEntry | null>(
    null
  );
  const [friendDash, setFriendDash] = useState<DashboardResponse | null>(null);
  const [loadingFriendDash, setLoadingFriendDash] = useState(false);
  const [modalTab, setModalTab] = useState<"overview" | "solves">("overview");
  const [recentSolvesList, setRecentSolvesList] = useState<RecentSolve[]>([]);
  const [loadingRecentSolves, setLoadingRecentSolves] = useState(false);
  const [selectedSolveBreakdown, setSelectedSolveBreakdown] = useState<RecentSolve | null>(null);
  const [avatarLoadError, setAvatarLoadError] = useState(false);

  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toastSolve, setToastSolve] = useState<{
    user_name: string;
    title: string;
    leetcode_url: string;
  } | null>(null);

  // Settings & Coffee Modal States
  const [showSettings, setShowSettings] = useState(false);
  const [showCoffeeModal, setShowCoffeeModal] = useState(false);
  const [newLeetcodeUsername, setNewLeetcodeUsername] = useState("");
  const [updatingUsername, setUpdatingUsername] = useState(false);
  const [settingsMsg, setSettingsMsg] = useState<string | null>(null);

  // Delete Account States
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Group Modal States
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);
  const [showDeleteGroupModal, setShowDeleteGroupModal] = useState(false);
  const [deletingGroup, setDeletingGroup] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<{ id: number; name: string } | null>(null);
  const [removingMember, setRemovingMember] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [groupActionBusy, setGroupActionBusy] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [shareMsg, setShareMsg] = useState<string | null>(null);
  const [showPointsHelp, setShowPointsHelp] = useState(false);
  const [kudosAllBusy, setKudosAllBusy] = useState(false);

  // Network Offline Listener & Dynamic OTA Config States
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [appConfig, setAppConfig] = useState<AppConfigResponse | null>(appConfigProp || null);

  useEffect(() => {
    if (appConfigProp) setAppConfig(appConfigProp);
  }, [appConfigProp]);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Fetch dynamic Over-The-Air app configuration & menus
    api.getAppConfig().then((cfg) => {
      if (cfg) setAppConfig(cfg);
    });

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  function handleShareGroup(groupName: string, code: string) {
    const inviteText = `Join my LeetStreak group "${groupName}"! Use Invite Code: ${code}`;
    navigator.clipboard.writeText(inviteText);
    setShareMsg("Copied Invite!");
    setTimeout(() => setShareMsg(null), 2500);
  }

  async function handleUpdateUsername(e: React.FormEvent) {
    e.preventDefault();
    if (!newLeetcodeUsername.trim()) return;
    setUpdatingUsername(true);
    setSettingsMsg(null);
    setError(null);
    try {
      const res = await api.updateLeetcodeUsername(userId, newLeetcodeUsername.trim());
      setSettingsMsg(`Updated username to @${res.leetcode_username}!`);
      await loadData(selectedTab);
      setTimeout(() => {
        setShowSettings(false);
        setSettingsMsg(null);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update username.");
    } finally {
      setUpdatingUsername(false);
    }
  }

  async function handleDeleteAccount(e: React.FormEvent) {
    e.preventDefault();
    if (!deletePassword) return;
    setDeletingAccount(true);
    setDeleteError(null);
    try {
      await api.deleteAccount(userId, deletePassword);
      setShowDeleteModal(false);
      setShowSettings(false);
      onResetUser();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Incorrect password. Account deletion failed.");
    } finally {
      setDeletingAccount(false);
    }
  }

  async function loadData(
    tab: BoardTab = selectedTab,
    sortMode: "points" | "streak" = sortBy
  ) {
    try {
      // 🚀 Parallelize all independent API calls to eliminate sequential network waterfalls!
      const boardPromise =
        tab === "global"
          ? api.leaderboard(userId, sortMode)
          : tab === "friends"
          ? api.friendsLeaderboard(userId, sortMode)
          : api.groupLeaderboard(tab, userId, sortMode);

      const [dashRes, myGroupsRes, boardRes, feedData] = await Promise.all([
        api.dashboard(userId).catch((err) => {
          if (err.message.includes("404") || err.message.includes("not found")) {
            onResetUser();
            return null;
          }
          throw err;
        }),
        api.myGroups(userId).catch(() => ({ groups: [] })),
        boardPromise.catch(() => null),
        fetch(`${API_BASE}/feed/recent-solves?limit=10`)
          .then((res) => (res.ok ? res.json() : []))
          .catch(() => []),
      ]);

      if (!dashRes) {
        setBoardLoading(false);
        return;
      }

      setDash(dashRes);
      if (myGroupsRes?.groups) setGroups(myGroupsRes.groups);
      if (boardRes) {
        setBoard(boardRes);
        setTabBoards((prev) => ({ ...prev, [String(tab)]: boardRes }));
        setStored(`codestreak_cached_board_${String(tab)}`, JSON.stringify(boardRes));
        setStored("codestreak_cached_board", JSON.stringify(boardRes));
      }
      setBoardLoading(false);
      if (Array.isArray(feedData)) setActivityFeed(feedData);
      setError(null);

      // Save stale-while-revalidate cache for instant 0ms load next time!
      setStored("codestreak_cached_dash", JSON.stringify(dashRes));

      // Update Chrome Extension Action Badge
      if (typeof chrome !== "undefined" && chrome.action && chrome.action.setBadgeText) {
        const badgeText = dashRes.today_count > 0 ? `🔥${dashRes.current_streak}` : `${dashRes.current_streak}`;
        chrome.action.setBadgeText({ text: badgeText });
        chrome.action.setBadgeBackgroundColor({ color: dashRes.today_count > 0 ? "#10b981" : "#6366f1" });
      }
    } catch (err) {
      setBoardLoading(false);
      const errMsg = err instanceof Error ? err.message : "";
      if (errMsg.includes("404") || errMsg.includes("User not found")) {
        onResetUser();
      } else {
        setError(err instanceof Error ? err.message : "Couldn't load dashboard.");
      }
    }
  }

  async function handleToggleKudos(toUserId: number) {
    if (!userId || toUserId === userId) return;

    let previousCount = 0;
    let previousHasKudosed = false;

    // 1. Update UI state INSTANTLY in 0ms (Optimistic Update)
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        entries: prev.entries.map((e) => {
          if (e.id === toUserId) {
            previousCount = e.kudos_count || 0;
            previousHasKudosed = !!e.has_kudosed;
            const nextHasKudosed = !e.has_kudosed;
            const delta = nextHasKudosed ? 1 : -1;
            const nextCount = Math.max(0, previousCount + delta);
            return { ...e, kudos_count: nextCount, has_kudosed: nextHasKudosed };
          }
          return e;
        }),
      };
    });

    // 2. Sync with server in background
    try {
      const res = await api.toggleKudos(toUserId, userId);
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          entries: prev.entries.map((e) =>
            e.id === toUserId
              ? { ...e, kudos_count: res.kudos_count, has_kudosed: res.has_kudosed }
              : e
          ),
        };
      });
    } catch (err) {
      console.error("Kudos background sync error, rolling back:", err);
      // Rollback on error
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          entries: prev.entries.map((e) =>
            e.id === toUserId
              ? { ...e, kudos_count: previousCount, has_kudosed: previousHasKudosed }
              : e
          ),
        };
      });
    }
  }

  async function handleKudosAll() {
    if (!userId || !board || !board.entries || !board.entries.length) return;
    const targetUserIds = board.entries
      .filter((e) => e.id !== userId && !e.has_kudosed)
      .map((e) => e.id);

    if (targetUserIds.length === 0) {
      setSyncMsg("All visible members already kudosed! 👏");
      setTimeout(() => setSyncMsg(null), 2500);
      return;
    }

    setKudosAllBusy(true);

    // Optimistically update visible entries
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        entries: prev.entries.map((e) => {
          if (targetUserIds.includes(e.id)) {
            return {
              ...e,
              kudos_count: (e.kudos_count || 0) + 1,
              has_kudosed: true,
            };
          }
          return e;
        }),
      };
    });

    try {
      await api.kudosAll(userId, targetUserIds);
      setSyncMsg(`Gave kudos to ${targetUserIds.length} member${targetUserIds.length === 1 ? "" : "s"}! 👏`);
      setTimeout(() => setSyncMsg(null), 2500);
    } catch (err) {
      console.error("Kudos All failed:", err);
      loadData(selectedTab, sortBy);
    } finally {
      setKudosAllBusy(false);
    }
  }

  async function fetchLeaderboardOnly(
    tab: BoardTab = selectedTab,
    sortMode: "points" | "streak" = sortBy
  ) {
    const tabKey = String(tab);

    // If cached in memory, use it instantly (0ms delay)
    if (tabBoards[tabKey]) {
      setBoard(tabBoards[tabKey]);
      setBoardLoading(false);
    } else {
      // Clear board immediately so old users vanish on click
      setBoard(null);
      setBoardLoading(true);
    }

    try {
      const boardPromise =
        tab === "global"
          ? api.leaderboard(userId, sortMode)
          : tab === "friends"
          ? api.friendsLeaderboard(userId, sortMode)
          : api.groupLeaderboard(tab, userId, sortMode);

      const boardRes = await boardPromise;
      if (boardRes) {
        setBoard(boardRes);
        setTabBoards((prev) => ({ ...prev, [tabKey]: boardRes }));
        setStored(`codestreak_cached_board_${tabKey}`, JSON.stringify(boardRes));
      }
    } catch (err) {
      console.error("Leaderboard fetch error:", err);
    } finally {
      setBoardLoading(false);
    }
  }

  // 1. Initial mount: load full app state (dashboard, groups, feed, active board)
  useEffect(() => {
    if (userId) {
      loadData(selectedTab, sortBy);
    }
  }, [userId]);

  // 2. Fast tab or sort switch: fetch ONLY the leaderboard endpoint (~100ms, old users vanish immediately!)
  useEffect(() => {
    if (userId) {
      fetchLeaderboardOnly(selectedTab, sortBy);
    }
  }, [selectedTab, sortBy]);

  async function handleSync() {
    setSyncing(true);
    setSyncMsg(null);
    setError(null);
    try {
      const res = await api.syncUser(userId);
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
      changeTab(group.id);
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
      changeTab(group.id);
      await loadData(group.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to join group.");
    } finally {
      setGroupActionBusy(false);
    }
  }

  async function handleDeleteGroup() {
    if (!activeGroup || !userId) return;
    setDeletingGroup(true);
    try {
      await api.deleteGroup(activeGroup.id, userId);
      const deletedId = activeGroup.id;
      setGroups((prev) => prev.filter((g) => g.id !== deletedId));
      setShowDeleteGroupModal(false);
      changeTab("global");
      setSyncMsg("Group deleted successfully.");
      setTimeout(() => setSyncMsg(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete group.");
    } finally {
      setDeletingGroup(false);
    }
  }

  function handlePromptRemoveMember(memberUserId: number, memberName: string) {
    setMemberToRemove({ id: memberUserId, name: memberName });
  }

  async function confirmRemoveMember() {
    if (!activeGroup || !userId || !memberToRemove) return;
    setRemovingMember(true);
    try {
      await api.removeMember(activeGroup.id, memberToRemove.id, userId);
      const targetId = memberToRemove.id;
      const targetName = memberToRemove.name;
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          entries: prev.entries.filter((e) => e.id !== targetId),
          total_users: Math.max(0, (prev.total_users || 1) - 1),
        };
      });
      setSyncMsg(`Removed ${targetName} from group.`);
      setMemberToRemove(null);
      setTimeout(() => setSyncMsg(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove member.");
    } finally {
      setRemovingMember(false);
    }
  }

  async function handleInspectFriend(entry: LeaderboardEntry) {
    setInspectedFriend(entry);
    setModalTab("overview");
    setLoadingFriendDash(true);
    setLoadingRecentSolves(true);
    try {
      const [friendData, solvesData] = await Promise.all([
        api.dashboard(entry.id).catch(() => null),
        api.recentSolves(entry.id, 10).catch(() => []),
      ]);
      setFriendDash(friendData);
      setRecentSolvesList(solvesData);
    } catch (err) {
      console.warn("Could not load friend detailed data", err);
    } finally {
      setLoadingFriendDash(false);
      setLoadingRecentSolves(false);
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
    selectedTab !== "global" && selectedTab !== "friends"
      ? groups.find((g) => String(g.id) === String(selectedTab))
      : null;

  const isGroupOwner = Boolean(
    activeGroup && Number(activeGroup.creator_id) === Number(userId)
  );

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
              href={`https://leetcode.com/u/${dash.leetcode_username}/`}
              target="_blank"
              rel="noreferrer"
              className="profile-handle"
            >
              @{dash.leetcode_username}
            </a>
          </div>
        </div>

        <div className="profile-actions">
          <button
            className="coffee-btn"
            onClick={() => setShowCoffeeModal(true)}
            title="Buy Me a Coffee ☕"
          >
            ☕
          </button>
          <button
            className="settings-btn"
            onClick={() => {
              setNewLeetcodeUsername(dash.leetcode_username);
              setSettingsMsg(null);
              setShowSettings(true);
            }}
            title="Account Settings (Change LeetCode Username)"
          >
            ⚙️
          </button>
          <button
            className="sync-btn"
            onClick={handleSync}
            disabled={syncing}
            title="Force sync latest LeetCode activity"
          >
            {syncing ? "Syncing…" : "🔄 Sync"}
          </button>
        </div>
      </div>

      {isOffline && (
        <div className="offline-banner">
          ⚠️ Connection lost — checking network…
        </div>
      )}
      {appConfig?.announcement && (
        <div className="announcement-banner">
          📢 {appConfig.announcement}
        </div>
      )}
      {syncMsg && <div className="sync-banner">{syncMsg}</div>}
      {error && <div className="error-banner">{error}</div>}

      {/* In-App Toast Notification Banner */}
      {toastSolve && (
        <div className="solve-toast-popup">
          <div className="toast-content">
            <span className="toast-flame">🔥</span>
            <div className="toast-text">
              <strong>{toastSolve.user_name}</strong> just solved <strong>"{toastSolve.title}"</strong> on LeetCode!
            </div>
            <a
              href={toastSolve.leetcode_url}
              target="_blank"
              rel="noreferrer"
              className="toast-link"
            >
              Open ↗
            </a>
            <button className="toast-close" onClick={() => setToastSolve(null)}>
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Unified M3 Hero Container Card */}
      <div className="hero-card">
        <div className="streak-hero">
          <span className="flame-icon">🔥</span>
          <span className="streak-count">{dash.current_streak}</span>
        </div>
        <div className="streak-label">DAY STREAK</div>

        <div className="stat-row">
          <Stat label="Today" value={dash.today_count} />
          <Stat label="This Week" value={dash.weekly_total} />
          <Stat label="This Month" value={dash.monthly_total} />
        </div>

        <div className="diff-pills">
          <span className="diff-pill easy">Easy {dash.easy_count}</span>
          <span className="diff-pill medium">Med {dash.medium_count}</span>
          <span className="diff-pill hard">Hard {dash.hard_count}</span>
          <span className="diff-pill total">Total {dash.easy_count + dash.medium_count + dash.hard_count}</span>
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
        <div className="tab-bar-container">
          <button
            className={`tab-btn ${selectedTab === "global" ? "active" : ""}`}
            onClick={() => changeTab("global")}
            title="Global Leaderboard (All platform users)"
          >
            🌐 Global
          </button>
          <button
            className={`tab-btn ${selectedTab === "friends" ? "active" : ""}`}
            onClick={() => changeTab("friends")}
            title="My Friends (All group members across your groups)"
          >
            👥 My Friends
          </button>
          {groups.map((g) => (
            <button
              key={g.id}
              className={`tab-btn ${selectedTab === g.id ? "active" : ""}`}
              onClick={() => changeTab(g.id)}
            >
              👥 {g.name}
            </button>
          ))}
        </div>

        {/* Leaderboard Sort & Group Code Control Bar */}
        <div className="sort-toggle-bar">
          <div className="sort-left-group">
            <span className="sort-label">Sort:</span>
            <div className="sort-btn-group">
              <button
                type="button"
                className={`sort-btn ${sortBy === "points" ? "active" : ""}`}
                onClick={() => setSortBy("points")}
                title="Sort leaderboard by total points"
              >
                ⭐ Points
              </button>
              <button
                type="button"
                className={`sort-btn ${sortBy === "streak" ? "active" : ""}`}
                onClick={() => setSortBy("streak")}
                title="Sort leaderboard by active daily streak"
              >
                🔥 Streak
              </button>
            </div>
          </div>

          <div className="sort-right-group">
            <button
              type="button"
              className="kudos-all-btn"
              onClick={handleKudosAll}
              disabled={kudosAllBusy}
              title="Give kudos to all visible members on this leaderboard!"
            >
              👏 {kudosAllBusy ? "Sending…" : "Kudos All"}
            </button>
          </div>
        </div>

        {/* Dedicated Group Management Bar */}
        {activeGroup && (
          <div className="group-info-bar">
            <div
              className="group-code-badge"
              onClick={() => handleCopyCode(activeGroup.code)}
              title={`Click to copy invite code (${activeGroup.code})`}
            >
              📋 Code: <strong>{activeGroup.code}</strong> {copiedCode ? "✓ Copied!" : ""}
            </div>
            {activeGroup.creator_id === userId && (
              <button
                type="button"
                className="group-delete-btn"
                onClick={() => setShowDeleteGroupModal(true)}
                title="Delete group (owner only)"
              >
                🗑️ Delete Group
              </button>
            )}
          </div>
        )}

        {/* Leaderboard List */}
        <ul className="leaderboard">
          {boardLoading || !board ? (
            <>
              <li className="leaderboard-skeleton-item">
                <div className="skeleton-avatar" />
                <div className="skeleton-line" />
              </li>
              <li className="leaderboard-skeleton-item">
                <div className="skeleton-avatar" />
                <div className="skeleton-line" />
              </li>
              <li className="leaderboard-skeleton-item">
                <div className="skeleton-avatar" />
                <div className="skeleton-line" />
              </li>
            </>
          ) : board.entries.length === 0 ? (
            <li className="centered muted py-3">No members in this group yet.</li>
          ) : (
            board.entries.map((e, index, arr) => {
              const prevEntry = index > 0 ? arr[index - 1] : null;
              const showGap = prevEntry && e.rank > prevEntry.rank + 1;
              return (
                <React.Fragment key={e.id}>
                  {showGap && (
                    <li className="leaderboard-gap" title="Ranks between Top 10 and your position">
                      <span>•••</span>
                    </li>
                  )}
                  <li
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
                      <span className="streak-mini">🔥{e.current_streak}d</span>
                      <span className="solves-badge" title="Questions solved this week">
                        📝{e.weekly_total}
                      </span>
                      <span
                        className="points-badge"
                        title={`Easy: ${e.easy_count} | Medium: ${e.medium_count} | Hard: ${e.hard_count}`}
                      >
                        ⭐{e.points !== null && e.points !== undefined ? Math.round(e.points) : "•••"}
                      </span>
                      <button
                        type="button"
                        className={`kudos-badge ${e.has_kudosed ? "active" : ""} ${e.id === userId ? "disabled" : ""}`}
                        title={
                          e.id === userId
                            ? "Your active streak"
                            : e.has_kudosed
                            ? "Click to remove kudos (resets daily IST)"
                            : "Click to give kudos (resets daily IST)"
                        }
                        onClick={(evt) => {
                          evt.stopPropagation();
                          handleToggleKudos(e.id);
                        }}
                      >
                        👍 {e.kudos_count || 0}
                      </button>
                    </div>

                    {isGroupOwner && Number(e.id) !== Number(userId) && activeGroup && (
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={(evt) => {
                          evt.stopPropagation();
                          handlePromptRemoveMember(e.id, e.name);
                        }}
                        title={`Remove ${e.name} from group`}
                      >
                        🗑️
                      </button>
                    )}
                  </li>
                </React.Fragment>
              );
            })
          )}
          {board && (
            <>
              {(board.total_users ?? 0) > (board.entries[board.entries.length - 1]?.rank ?? 0) && (
                <li className="leaderboard-gap" title="More registered users in squad">
                  <span>•••</span>
                </li>
              )}
              <li className="leaderboard-total-row">
                <span>
                  {selectedTab === "global"
                    ? `⚔️ ${board.total_users ?? board.entries.length} algorithm warriors on leetstreak`
                    : selectedTab === "friends"
                    ? `🧠 ${board.total_users ?? board.entries.length} algorithm compadres in your squad`
                    : `⚔️ ${board.total_users ?? board.entries.length} devs grinding in this group`}
                </span>
              </li>
            </>
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
              title="Close modal"
            >
              ✕
            </button>
            <div className="modal-header">
              {inspectedFriend.avatar_url && !avatarLoadError ? (
                <img
                  src={inspectedFriend.avatar_url}
                  alt={inspectedFriend.name}
                  className="modal-avatar"
                  onError={() => setAvatarLoadError(true)}
                />
              ) : (
                <div className="avatar-placeholder lg">
                  {inspectedFriend.name ? inspectedFriend.name[0].toUpperCase() : "U"}
                </div>
              )}
              <div className="modal-user-info">
                <h3>{inspectedFriend.name}</h3>
                <a
                  href={`https://leetcode.com/u/${inspectedFriend.leetcode_username}/`}
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
              <span
                className="modal-points-tag"
                title={`Easy: ${inspectedFriend.easy_count} | Medium: ${inspectedFriend.medium_count} | Hard: ${inspectedFriend.hard_count}`}
              >
                ⭐ {inspectedFriend.points ?? (inspectedFriend.easy_count * 1 + inspectedFriend.medium_count * 3 + inspectedFriend.hard_count * 6)} pts
              </span>
            </div>

            {/* Modal Tab Bar */}
            <div className="modal-tab-bar">
              <button
                className={`modal-tab-btn ${modalTab === "overview" ? "active" : ""}`}
                onClick={() => setModalTab("overview")}
              >
                📊 Overview
              </button>
              <button
                className={`modal-tab-btn ${modalTab === "solves" ? "active" : ""}`}
                onClick={() => setModalTab("solves")}
              >
                📝 Recent Solves ({recentSolvesList.length})
              </button>
            </div>

            {modalTab === "overview" ? (
              <>
                <div className="section-title text-center mb-1">QUESTIONS SOLVED</div>
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
                  <span className="diff-pill total">
                    Total {inspectedFriend.easy_count + inspectedFriend.medium_count + inspectedFriend.hard_count}
                  </span>
                </div>

                {/* Material UI 7-Day Activity Calendar Card */}
                {loadingFriendDash ? (
                  <div className="centered muted tiny py-2">Loading activity calendar…</div>
                ) : friendDash ? (
                  <div className="profile-calendar-card">
                    <div className="profile-calendar-title">
                      <span>📅</span>
                      <span>LAST 7 DAYS ACTIVITY</span>
                    </div>
                    <div className="profile-heatmap">
                      {friendDash.last_7_days.map((d, i) => {
                        const solved = d.problems_solved;
                        const maxSolved = Math.max(1, ...friendDash.last_7_days.map((x) => x.problems_solved));
                        const heightPct = Math.min(100, Math.max(14, (solved / maxSolved) * 100));
                        return (
                          <div className="profile-heat-col" key={d.date}>
                            <div className="profile-bar-track">
                              <div
                                className={`profile-heat-bar ${solved > 0 ? "active" : ""}`}
                                style={{
                                  height: `${heightPct}%`,
                                }}
                                title={`${d.date}: ${solved} problem${solved === 1 ? "" : "s"} solved`}
                              />
                            </div>
                            <span className="profile-heat-day">{dayLabels[i]}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="modal-solves-container">
                <div className="section-title mb-1">Last 10 Solved Questions</div>
                {loadingRecentSolves ? (
                  <div className="centered muted tiny py-3">Loading solves…</div>
                ) : recentSolvesList.length === 0 ? (
                  <div className="centered muted tiny py-3">No recent solves recorded yet.</div>
                ) : (
                  <ul className="recent-solves-list">
                    {recentSolvesList.map((s, idx) => {
                      const problemUrl = s.leetcode_url || `https://leetcode.com/problems/${s.title_slug}`;
                      return (
                        <li
                          key={idx}
                          className="solve-item"
                          onClick={() => setSelectedSolveBreakdown(s)}
                          title="Click to view points breakdown"
                        >
                          <span className="solve-bullet">✔</span>
                          <div className="solve-info">
                            <span className="solve-title">
                              {s.title}
                            </span>
                          </div>
                          <a
                            href={problemUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="solve-external-link"
                            onClick={(e) => e.stopPropagation()}
                            title="Open on LeetCode"
                          >
                            ↗
                          </a>
                          <button
                            type="button"
                            className="solve-points-badge"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedSolveBreakdown(s);
                            }}
                            title="Click to see how these points were calculated"
                          >
                            ⭐ {s.points_earned ?? s.breakdown?.points_earned ?? 0} pts
                          </button>
                          <span className="solve-time">{s.relative_time}</span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}

          </div>
        </div>
      )}

      {/* Remove Member Confirmation Modal */}
      {memberToRemove && activeGroup && (
        <div className="modal-overlay" onClick={() => setMemberToRemove(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="danger-title">🗑️ Remove Member</h3>
              <button
                className="modal-close"
                onClick={() => setMemberToRemove(null)}
                title="Cancel"
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: "13px", color: "var(--md-sys-color-on-surface-variant)", margin: "12px 0", lineHeight: "1.4" }}>
              Are you sure you want to remove <strong>{memberToRemove.name}</strong> from <strong>{activeGroup.name}</strong>?
            </p>
            <div className="modal-actions-row">
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setMemberToRemove(null)}
                disabled={removingMember}
              >
                Cancel
              </button>
              <button
                type="button"
                className="danger-btn modal-action-btn"
                onClick={confirmRemoveMember}
                disabled={removingMember}
              >
                {removingMember ? "Removing…" : "Confirm & Remove"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Account Settings Modal */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>⚙️ Account Settings</h3>
              <button
                className="modal-close"
                onClick={() => setShowSettings(false)}
                title="Close settings"
              >
                ✕
              </button>
            </div>

            {settingsMsg && <div className="sync-banner">{settingsMsg}</div>}

            <div style={{ marginBottom: "16px" }}>
              <button
                type="button"
                className="secondary-btn modal-action-btn"
                onClick={() => {
                  setShowSettings(false);
                  onResetUser();
                }}
              >
                🚪 Log Out
              </button>
            </div>

            <form onSubmit={handleUpdateUsername} className="modal-form">
              <div className="modal-field">
                <label>
                  <span>LeetCode Username</span>
                  <input
                    value={newLeetcodeUsername}
                    onChange={(e) => setNewLeetcodeUsername(e.target.value)}
                    placeholder="e.g. neal_wu"
                    required
                  />
                </label>
              </div>

              <button
                type="submit"
                className="primary-btn modal-action-btn"
                disabled={updatingUsername}
              >
                {updatingUsername ? "Verifying & Updating…" : "Save New Username"}
              </button>
            </form>

            <div className="danger-zone">
              <hr className="modal-divider" />
              <div className="danger-zone-header">
                <span className="danger-zone-title">Danger Zone</span>
              </div>
              <button
                type="button"
                className="danger-btn modal-action-btn"
                onClick={() => {
                  setShowSettings(false);
                  setDeletePassword("");
                  setDeleteError(null);
                  setShowDeleteModal(true);
                }}
              >
                🗑️ Delete Account
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Group Confirmation Modal */}
      {showDeleteGroupModal && activeGroup && (
        <div className="modal-overlay" onClick={() => setShowDeleteGroupModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="danger-title">🗑️ Delete Group</h3>
              <button
                className="modal-close"
                onClick={() => setShowDeleteGroupModal(false)}
                title="Cancel"
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: "13px", color: "var(--md-sys-color-on-surface-variant)", margin: "12px 0", lineHeight: "1.4" }}>
              Are you sure you want to delete <strong>{activeGroup.name}</strong>? All members will be removed and this group will be deleted permanently.
            </p>
            <div className="modal-actions-row">
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setShowDeleteGroupModal(false)}
                disabled={deletingGroup}
              >
                Cancel
              </button>
              <button
                type="button"
                className="danger-btn modal-action-btn"
                onClick={handleDeleteGroup}
                disabled={deletingGroup}
              >
                {deletingGroup ? "Deleting…" : "Delete Group"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="danger-title">🗑️ Delete Account</h3>
              <button
                className="modal-close"
                onClick={() => setShowDeleteModal(false)}
                title="Cancel"
              >
                ✕
              </button>
            </div>

            <p className="modal-description danger-text">
              This action is permanent and cannot be undone. All your streaks, points, and group memberships will be deleted.
            </p>

            {deleteError && <div className="error-banner">{deleteError}</div>}

            <form onSubmit={handleDeleteAccount} className="modal-form">
              <div className="modal-field">
                <label>
                  <span>Enter Password to Confirm</span>
                  <input
                    type="password"
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    placeholder="Account password"
                    required
                  />
                </label>
              </div>

              <div className="modal-actions-row">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setShowDeleteModal(false)}
                  disabled={deletingAccount}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="danger-btn modal-action-btn"
                  disabled={deletingAccount || !deletePassword}
                >
                  {deletingAccount ? "Deleting…" : "Confirm & Delete"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Buy Me a Coffee Modal */}
      {showCoffeeModal && (
        <div className="modal-overlay" onClick={() => setShowCoffeeModal(false)}>
          <div className="modal-content coffee-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>☕ Buy Me a Coffee</h3>
              <button
                className="modal-close"
                onClick={() => setShowCoffeeModal(false)}
                title="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="coffee-modal-body">
              <div className="qr-container">
                <img src="upi_qr.png" alt="UPI QR Code" className="upi-qr-img" />
              </div>

              <div className="coffee-text-box">
                <p className="coffee-gratitude-title">💛 Thank you for using LeetStreak!</p>
                <p className="coffee-gratitude-text">
                  If LeetStreak helps you and your friends stay consistent on LeetCode, consider buying me a coffee! Your support fuels server hosting, live features, and continuous updates. Every cup is deeply appreciated! ☕
                </p>
              </div>

              <div className="upi-badge-box">
                <span className="tiny muted uppercase">Scan with any UPI App</span>
                <span className="upi-app-icons">GPay • PhonePe • Paytm • BHIM</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Solve Points Breakdown Modal */}
      {selectedSolveBreakdown && (
        <div className="modal-overlay" onClick={() => setSelectedSolveBreakdown(null)}>
          <div className="modal-content solve-breakdown-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-heading">⭐ Points Breakdown</h3>
              <button
                className="modal-close"
                onClick={() => setSelectedSolveBreakdown(null)}
                title="Close"
              >
                ✕
              </button>
            </div>

            <div className="question-title-card">
              <span className="tiny muted">QUESTION</span>
              <a
                href={
                  selectedSolveBreakdown.leetcode_url ||
                  `https://leetcode.com/problems/${selectedSolveBreakdown.title_slug}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="question-title-text"
                title="Click to open question on LeetCode"
              >
                {selectedSolveBreakdown.title} ↗
              </a>
            </div>

            {/* Base Problem Score Card */}
            <div className="breakdown-card">
              <div className="breakdown-card-header">
                <span className="card-label">1. Base Problem Score</span>
                {selectedSolveBreakdown.breakdown?.contest_rating ? (
                  <span className="badge-contest">ZeroTrac Elo {Math.round(selectedSolveBreakdown.breakdown.contest_rating)}</span>
                ) : (
                  <span className="badge-diff">{selectedSolveBreakdown.breakdown?.difficulty || "Medium"} Category</span>
                )}
              </div>

              {selectedSolveBreakdown.breakdown?.contest_rating ? (
                <div className="breakdown-row">
                  <span className="row-label">Contest Base Points (Elo / 100):</span>
                  <span className="row-val main-val">{selectedSolveBreakdown.breakdown.base_points} pts</span>
                </div>
              ) : (
                <>
                  <div className="breakdown-row">
                    <span className="row-label">Category Base Points ({selectedSolveBreakdown.breakdown?.difficulty || "Medium"}):</span>
                    <span className="row-val">{selectedSolveBreakdown.breakdown?.raw_base_points ?? selectedSolveBreakdown.breakdown?.base_points ?? 0} pts</span>
                  </div>
                  <div className="breakdown-row">
                    <span className="row-label">Acceptance Rate Adjustment:</span>
                    <span className={`row-val ${(selectedSolveBreakdown.breakdown?.ac_adjustment || 0) >= 0 ? "text-green" : "text-red"}`}>
                      {(selectedSolveBreakdown.breakdown?.ac_adjustment || 0) >= 0 ? "+" : ""}
                      {selectedSolveBreakdown.breakdown?.ac_adjustment ?? 0} pts
                      {selectedSolveBreakdown.breakdown?.ac_rate !== undefined && selectedSolveBreakdown.breakdown?.ac_rate !== null && (
                        <span className="tiny muted"> ({selectedSolveBreakdown.breakdown.ac_rate}% AC)</span>
                      )}
                    </span>
                  </div>
                  <div className="breakdown-subtotal-line">
                    <span className="row-label font-bold">Effective Base Score:</span>
                    <span className="row-val font-bold">{selectedSolveBreakdown.breakdown?.base_points} pts</span>
                  </div>
                </>
              )}
            </div>

            {/* Bonuses & Multipliers Card */}
            <div className="breakdown-card">
              <div className="breakdown-card-header">
                <span className="card-label">2. Bonuses & Multipliers</span>
              </div>
              <div className="breakdown-row">
                <span className="row-label">Daily Challenge Bonus:</span>
                <span className={`row-val ${(selectedSolveBreakdown.breakdown?.daily_bonus || 0) > 0 ? "text-amber" : "text-muted"}`}>
                  +{(selectedSolveBreakdown.breakdown?.daily_bonus || 0)} pts
                </span>
              </div>
              <div className="breakdown-row">
                <span className="row-label">Streak Multiplier:</span>
                <span className="row-val text-violet">
                  {selectedSolveBreakdown.breakdown?.streak_multiplier || 1.0}× <span className="tiny muted">({selectedSolveBreakdown.breakdown?.streak_days || 0}d streak)</span>
                </span>
              </div>
            </div>

            {/* Total Score Box */}
            <div className="breakdown-total-card">
              <div className="total-title-group">
                <div className="total-title">Total Points Earned</div>
                <div className="tiny muted">Base + Bonuses × Streak</div>
              </div>
              <div className="total-score-badge">
                ⭐ {selectedSolveBreakdown.points_earned ?? selectedSolveBreakdown.breakdown?.points_earned ?? 0} pts
              </div>
            </div>
            <div className="modal-footer centered-footer">
              <button
                type="button"
                className="primary-btn center-btn"
                onClick={() => setSelectedSolveBreakdown(null)}
              >
                Close
              </button>
            </div>
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

function PointsHelpModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content points-help-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>How Points Work</h3>
          <button className="modal-close" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <div className="help-section-list">
          {/* Section 1: Base Points */}
          <div className="help-section">
            <h4 className="help-section-title">1. Base Problem Points</h4>
            <p className="help-text">
              Points per problem are calculated based on official LeetCode difficulty data:
            </p>
            <ul className="help-bullet-list">
              <li>
                <strong>Contest Rating (Primary):</strong> Sourced from <strong>ZeroTrac</strong> contest ratings. Base points equal <code>Rating / 100</code> (e.g. 1550 rating = <strong>15.5 pts</strong>, 2400 rating = <strong>24.0 pts</strong>).
              </li>
              <li>
                <strong>Non-Contest Problems:</strong> Evaluated using difficulty category defaults (Easy: <strong>8 pts</strong>, Medium: <strong>15 pts</strong>, Hard: <strong>24 pts</strong>) scaled inversely by acceptance rate (lower acceptance rate yields higher points).
              </li>
            </ul>
          </div>

          {/* Section 2: Bonus Rewards */}
          <div className="help-section">
            <h4 className="help-section-title">2. Bonus Rewards</h4>
            <div className="bonus-row">
              <div className="bonus-box">
                <span className="bonus-label">Daily Challenge</span>
                <span className="bonus-val">+5 Pts</span>
              </div>
            </div>
          </div>

          {/* Section 3: Streak Multiplier */}
          <div className="help-section">
            <h4 className="help-section-title">3. Streak Multiplier</h4>
            <p className="help-text">
              Maintaining an active daily streak boosts your total points up to <strong>+10% max</strong> (scaling linearly from 1.00× on Day 1 to 1.10× at Day 30+).
            </p>
          </div>
        </div>

        <div className="modal-footer centered-footer">
          <button type="button" className="primary-btn center-btn" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}


