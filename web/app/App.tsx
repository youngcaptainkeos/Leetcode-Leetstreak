import { useSyncJob } from "./useSyncJob";
import { formatPoints } from "../../shared/points";
import React, { useEffect, useState } from "react";
import {
  api,
  ApiError,
  showGlobalLeaderboard,
  API_BASE,
  DashboardResponse,
  LeaderboardResponse,
  LeaderboardEntry,
  GroupResponse,
  RecentSolve,
  AppConfigResponse,
  DynamicMenuItem,
} from "./lib/api";
import { getStored, setStored, clearStored, getAccountStored, setAccountStored } from "./storage";
import { navigate, setSessionUserId } from "./session";
import { IS_WEBSITE, assetUrl } from "./lib/runtime";

type BoardTab = "global" | "friends" | number;
export type AuthMode = "login" | "register" | "forgot";

export default function App({ userId, onRegistered, onLogout, authMode = "login" }: {
  userId: number | null;
  onRegistered: (id: number, token?: string) => void;
  onLogout: () => void;
  authMode?: AuthMode;
}) {
  const [error, setError] = useState<string | null>(null);
  const [showPointsHelp, setShowPointsHelp] = useState(false);
  return (
    <div className={`app ${userId ? "workspace-app" : "auth-app"}`}>
      {userId && <div className="workspace-heading">
        <div><span className="web-eyebrow">YOUR DAILY PRACTICE</span><h1>Your coding workspace</h1><p>A little progress today. A stronger habit tomorrow.</p></div>
        <button className="help-btn" onClick={() => setShowPointsHelp(true)}>How points work ↗</button>
      </div>}
      {showPointsHelp && <PointsHelpModal onClose={() => setShowPointsHelp(false)} />}
      {userId ? <Dashboard key={userId} userId={userId} onResetUser={onLogout} /> :
        <Onboarding initialMode={authMode} onRegistered={onRegistered} onError={setError} />}
      {error && <div className="error-banner" role="alert">{error}</div>}
    </div>
  );
}

function Onboarding({
  initialMode,
  onRegistered,
  onError,
}: {
  initialMode: AuthMode;
  onRegistered: (id: number, token?: string) => void;
  onError: (e: string | null) => void;
}) {
  const [authMode, setAuthMode] = useState<AuthMode>(initialMode);
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [signupCodeforces, setSignupCodeforces] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [forgotStep, setForgotStep] = useState<1 | 2>(1);
  const [sentEmail, setSentEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [draftsLoaded, setDraftsLoaded] = useState(false);
  const [enableGlobalLeaderboard, setEnableGlobalLeaderboard] = useState(true);
  const [showUsernameHelpModal, setShowUsernameHelpModal] = useState(false);

  useEffect(() => { setAuthMode(initialMode); onError(null); }, [initialMode]);

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
      if (IS_WEBSITE) {
        const path = window.location.pathname;
        setAuthMode(path === "/register" ? "register" : path === "/forgot-password" ? "forgot" : "login");
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
    navigate(mode === "forgot" ? "/forgot-password" : `/${mode}`, true);
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
      if (!res.access_token) throw new Error("Please update the app and sign in again.");
      onRegistered(res.id, res.access_token);
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
      const res = await api.register(name.trim(), username.trim(), email.trim(), password, enableGlobalLeaderboard, signupCodeforces);
      await clearStored(AUTH_STORAGE_KEYS);
      if (!res.access_token) throw new Error("Please update the app and sign in again.");
      onRegistered(res.id, res.access_token);
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
      setSentEmail("your registered email");
      setForgotStep(2);
      setSuccessMsg(res.message);
      await setStored("codestreak_auth_mode", "forgot");
      await setStored("codestreak_forgot_step", "2");
      await clearStored(["codestreak_sent_email"]);
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
      if (!res.access_token) throw new Error("Please update the app and sign in again.");
      onRegistered(res.id, res.access_token);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="onboarding">
      <div className="onboarding-welcome">
        <img src={assetUrl("logo_with_text.png")} alt="LeetStreak" className="onboarding-logo-img" />
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

            <button
              type="button"
              className="username-help-link-btn"
              onClick={() => setShowUsernameHelpModal(true)}
            >
              💡 Need help finding your LeetCode username?
            </button>

            <label>
              <span>Codeforces username · optional</span>
              <input aria-label="Codeforces username (optional)" value={signupCodeforces} onChange={e => setSignupCodeforces(e.target.value)} placeholder="Leave blank or enter your handle" minLength={3} maxLength={24} />
            </label>
            <p className="tiny muted">Optional: include Codeforces solves in your points and streak. You can also connect it later in Settings.</p>

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
                placeholder="At least 15 characters"
                minLength={15}
                maxLength={100}
                required
              />
            </label>

            <div
              className={`auth-leaderboard-card ${enableGlobalLeaderboard ? "active" : ""}`}
              onClick={() => setEnableGlobalLeaderboard((prev) => !prev)}
              role="button"
              tabIndex={0}
              title={
                enableGlobalLeaderboard
                  ? "Hide Global leaderboard on your home page"
                  : "Show Global leaderboard on your home page"
              }
              onKeyDown={(e) => {
                if (e.key === " " || e.key === "Enter") {
                  e.preventDefault();
                  setEnableGlobalLeaderboard((prev) => !prev);
                }
              }}
            >
              <div className="auth-leaderboard-left">
                <span className="auth-leaderboard-icon">🌐</span>
                <div className="auth-leaderboard-text">
                  <span className="auth-leaderboard-title">
                    Show Global leaderboard
                  </span>
                  <span className="auth-leaderboard-desc">
                    {enableGlobalLeaderboard
                      ? "Shown here; everyone participates"
                      : "Hidden here; you still participate"}
                  </span>
                </div>
              </div>

              <div
                className={`auth-toggle-track ${enableGlobalLeaderboard ? "on" : "off"}`}
                aria-hidden="true"
              >
                <div className="auth-toggle-thumb" />
              </div>
            </div>

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
                    placeholder="At least 15 characters"
                    minLength={15}
                    maxLength={100}
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

      <div className="auth-legal-footer" style={{ textAlign: "center", marginTop: "14px", fontSize: "11px", color: "var(--text-muted, #94a3b8)", lineHeight: "1.5" }}>
        By continuing, you agree to our{" "}
        <a href="https://codestreak-api.onrender.com/terms" target="_blank" rel="noreferrer" style={{ color: "#38bdf8", textDecoration: "none" }}>
          Terms &amp; EULA
        </a>{" "}
        and{" "}
        <a href="https://codestreak-api.onrender.com/privacy" target="_blank" rel="noreferrer" style={{ color: "#38bdf8", textDecoration: "none" }}>
          Privacy Policy
        </a>
        .<br />
        <span style={{ fontSize: "10px", opacity: 0.75 }}>
          Independent project. Not affiliated with LeetCode LLC.
        </span>
      </div>

      {showUsernameHelpModal && (
        <LeetcodeUsernameHelpModal onClose={() => setShowUsernameHelpModal(false)} />
      )}
    </div>
  );
}

interface ActivityFeedItem {
  platform?: "leetcode" | "codeforces";
  problem_url?: string;
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
  const getStored = (key: string) => getAccountStored(userId, key);
  const setStored = (key: string, value: string) => setAccountStored(userId, key, value);
  const [ownSolves, setOwnSolves] = useState<RecentSolve[]>([]);
  const [ownSolvesError, setOwnSolvesError] = useState(false);
  const [ownSolvesLoading, setOwnSolvesLoading] = useState(true);
  async function loadOwnSolves() {
    setOwnSolvesLoading(true);
    try {
      setOwnSolves(await api.recentSolves(userId, 8));
      setOwnSolvesError(false);
    } catch {
      setOwnSolvesError(true);
    } finally {
      setOwnSolvesLoading(false);
    }
  }
  useEffect(() => { void loadOwnSolves(); }, [userId]);
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
      const cachedDash = await getStored("codestreak_cached_dash");
      let cachedDashObj: DashboardResponse | null = null;
      if (cachedDash) {
        try {
          cachedDashObj = JSON.parse(cachedDash);
          setDash(cachedDashObj);
        } catch (e) {}
      }

      let activeTabKey = "global";
      if (cachedDashObj && !showGlobalLeaderboard(cachedDashObj)) {
        activeTabKey = "friends";
        setSelectedTab("friends");
      } else if (storedTab) {
        if (storedTab === "global" || storedTab === "friends") {
          setSelectedTab(storedTab);
          activeTabKey = storedTab;
        } else if (!isNaN(Number(storedTab))) {
          setSelectedTab(Number(storedTab));
          activeTabKey = storedTab;
        }
      }
      // Instant 0ms stale-while-revalidate cached rendering
      const cachedBoard = await getStored(`codestreak_cached_board_${activeTabKey}`) || await getStored("codestreak_cached_board");
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
  const [profileError, setProfileError] = useState("");
  const [modalTab, setModalTab] = useState<"overview" | "solves">("overview");
  const [recentSolvesList, setRecentSolvesList] = useState<RecentSolve[]>([]);
  const [loadingRecentSolves, setLoadingRecentSolves] = useState(false);
  const [selectedSolveBreakdown, setSelectedSolveBreakdown] = useState<RecentSolve | null>(null);
  const [avatarLoadError, setAvatarLoadError] = useState(false);

  const syncJob = useSyncJob(userId);
  const syncing = syncJob.active || syncJob.submitting;
  const syncCooldownKey = `codestreak_account_${userId}:sync_retry_at`;
  const [syncRetryAt, setSyncRetryAt] = useState(0);
  const [syncClock, setSyncClock] = useState(Date.now);
  const [syncCooldownReady, setSyncCooldownReady] = useState(false);
  const syncCooldown = Math.max(0, Math.ceil((syncRetryAt - syncClock) / 1000));
  useEffect(() => {
    let active = true;
    setSyncCooldownReady(false);
    void getStored(syncCooldownKey).then(saved => {
      if (!active) return;
      const deadline = Number(saved);
      setSyncRetryAt(Number.isFinite(deadline) && deadline > Date.now() ? deadline : 0);
      setSyncClock(Date.now());
      setSyncCooldownReady(true);
    }).catch(() => { if (active) setSyncCooldownReady(true); });
    return () => { active = false; };
  }, [syncCooldownKey]);
  useEffect(() => {
    if (syncRetryAt <= Date.now()) return;
    const timer = setInterval(() => {
      const now = Date.now();
      setSyncClock(now);
      if (now >= syncRetryAt) clearInterval(timer);
    }, 1000);
    return () => clearInterval(timer);
  }, [syncRetryAt]);
  async function setSyncCooldown(seconds: number) {
    const now = Date.now();
    const deadline = now + seconds * 1000;
    setSyncRetryAt(deadline);
    setSyncClock(now);
    // Store the expiry, not a decrementing counter, so time passes while closed.
    await setStored(syncCooldownKey, String(deadline)).catch(() => undefined);
  }
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toastSolve, setToastSolve] = useState<{
    user_name: string;
    title: string;
    leetcode_url: string;
  } | null>(null);

  // Settings & Coffee Modal States
  const [showSettings, setShowSettings] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [changedPassword, setChangedPassword] = useState("");
  const [securityBusy, setSecurityBusy] = useState(false);
  const [transferTarget, setTransferTarget] = useState("");
  const [transferBusy, setTransferBusy] = useState(false);
  useEffect(() => { if (!showSettings) { setCurrentPassword(""); setChangedPassword(""); } }, [showSettings]);
  const [showCoffeeModal, setShowCoffeeModal] = useState(false);
  useEffect(() => {
    const openSettings = () => {
      setNewLeetcodeUsername(dash?.leetcode_username || "");
      setSettingsMsg(null);
      setShowSettings(true);
    };
    window.addEventListener("leetstreak:settings", openSettings);
    return () => window.removeEventListener("leetstreak:settings", openSettings);
  }, [dash?.leetcode_username]);
  const [showUsernameHelpModal, setShowUsernameHelpModal] = useState(false);
  const [newLeetcodeUsername, setNewLeetcodeUsername] = useState("");
  const [newCodeforcesUsername, setNewCodeforcesUsername] = useState("");
  const [updatingCodeforces, setUpdatingCodeforces] = useState(false);
  const [updatingUsername, setUpdatingUsername] = useState(false);
  const [togglingLeaderboard, setTogglingLeaderboard] = useState(false);
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

  async function handleUpdateCodeforces(e: React.FormEvent) {
    e.preventDefault();
    if (!newCodeforcesUsername.trim()) return;
    setUpdatingCodeforces(true); setSettingsMsg(null);
    try {
      const result = await api.updateCodeforcesUsername(userId, newCodeforcesUsername.trim());
      setSettingsMsg(`Connected @${result.codeforces_username}. Public solves and points are syncing automatically.`);
      setNewCodeforcesUsername("");
      await loadData(selectedTab);
    } catch (err) {
      setSettingsMsg(err instanceof Error ? err.message : "Could not connect Codeforces.");
    } finally { setUpdatingCodeforces(false); }
  }

  useEffect(() => {
    if (!dash?.codeforces_username || dash.codeforces_last_sync || dash.codeforces_sync_error) return;
    const interval = setInterval(() => { void loadData(selectedTab); }, 5000);
    return () => clearInterval(interval);
  }, [dash?.codeforces_username, dash?.codeforces_last_sync, dash?.codeforces_sync_error, selectedTab]);

  async function handleChangePassword(event: React.FormEvent) {
    event.preventDefault();
    setSecurityBusy(true); setSettingsMsg(null);
    try {
      const result = await api.changePassword(userId, currentPassword, changedPassword);
      // Dashboard storage is account-scoped; credentials belong to the session.
      setSessionUserId(userId, result.access_token);
      setCurrentPassword(""); setChangedPassword("");
      setSettingsMsg("Password changed. Your other sessions have been signed out.");
    } catch (error) { setSettingsMsg(error instanceof Error ? error.message : "Could not change password."); }
    finally { setSecurityBusy(false); }
  }

  async function handleRevokeSessions() {
    setSecurityBusy(true); setSettingsMsg(null);
    try { await api.revokeSessions(userId); onResetUser(); }
    catch (error) { setSettingsMsg(error instanceof Error ? error.message : "Could not sign out sessions."); }
    finally { setSecurityBusy(false); }
  }

  async function handleTransferGroup() {
    if (!activeGroup || !transferTarget) return;
    const selected = activeGroup.members.find(member => String(member.id) === transferTarget);
    if (!selected || !window.confirm(`Transfer ownership to ${selected.name}? They will control group management.`)) return;
    setTransferBusy(true);
    try { await api.transferGroup(activeGroup.id, selected.id); setTransferTarget(""); await loadData(selectedTab); }
    catch (error) { setError(error instanceof Error ? error.message : "Could not transfer ownership."); }
    finally { setTransferBusy(false); }
  }

  async function handleToggleGlobalLeaderboard() {
    if (!dash) return;
    const currentEnabled = showGlobalLeaderboard(dash);
    const nextState = !currentEnabled;
    setTogglingLeaderboard(true);
    setSettingsMsg(null);
    try {
      await api.updateSettings(userId, { show_global_leaderboard: nextState });
      const updatedDash = { ...dash, show_global_leaderboard: nextState };
      setDash(updatedDash);
      setStored("codestreak_cached_dash", JSON.stringify(updatedDash));
      setSettingsMsg(
        nextState
          ? "Global view shown. Everyone still participates."
          : "Global view hidden here. You still participate."
      );
      setTimeout(() => setSettingsMsg(null), 3000);

      // If user disabled global leaderboard and is currently on global tab, redirect to friends
      if (!nextState && selectedTab === "global") {
        changeTab("friends");
      }
    } catch (err) {
      setSettingsMsg(err instanceof Error ? err.message : "Failed to update settings.");
    } finally {
      setTogglingLeaderboard(false);
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
        api.activityFeed().catch(() => []),
      ]);

      if (!dashRes) {
        setBoardLoading(false);
        return;
      }

      setDash(dashRes);
      if (!showGlobalLeaderboard(dashRes) && tab === "global") {
        changeTab("friends");
        return;
      }
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

    const activeTabKey = String(selectedTab);
    const updatedEntries = board.entries.map((e) => {
      if (targetUserIds.includes(e.id)) {
        return {
          ...e,
          kudos_count: (e.kudos_count || 0) + 1,
          has_kudosed: true,
        };
      }
      return e;
    });

    const newBoard = { ...board, entries: updatedEntries };

    setBoard(newBoard);
    setTabBoards((prev) => ({ ...prev, [activeTabKey]: newBoard }));
    setStored(`codestreak_cached_board_${activeTabKey}`, JSON.stringify(newBoard));
    setStored("codestreak_cached_board", JSON.stringify(newBoard));

    try {
      await api.kudosAll(userId, targetUserIds);
      setSyncMsg(`Gave kudos to ${targetUserIds.length} member${targetUserIds.length === 1 ? "" : "s"}! 👏`);
      setTimeout(() => setSyncMsg(null), 2500);

      const freshBoard = await (
        selectedTab === "global"
          ? api.leaderboard(userId, sortBy)
          : selectedTab === "friends"
          ? api.friendsLeaderboard(userId, sortBy)
          : api.groupLeaderboard(selectedTab, userId, sortBy)
      );

      if (freshBoard) {
        setBoard(freshBoard);
        setTabBoards((prev) => ({ ...prev, [activeTabKey]: freshBoard }));
        setStored(`codestreak_cached_board_${activeTabKey}`, JSON.stringify(freshBoard));
      }
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

  useEffect(() => {
    if (syncJob.error) setSyncMsg(syncJob.error);
    else if (syncJob.active) setSyncMsg(null);
    if (syncJob.retryAfter > 0) void setSyncCooldown(syncJob.retryAfter);
  }, [syncJob.error, syncJob.retryAfter]);

  useEffect(() => {
    const job = syncJob.finished;
    if (!job) return;
    if (job.state === "failed") {
      setError(job.message || "Sync could not finish. Please try again in a minute.");
      void setSyncCooldown(60);
      return;
    }
    setError(null);
    setSyncMsg(job.message || (job.new_solves > 0 ? `Synced! ${job.new_solves} new solve(s) added.` : "Your account is up to date."));
    void (async () => { await Promise.all([loadData(), loadOwnSolves()]); })();
    const timer = setTimeout(() => setSyncMsg(null), 5000);
    return () => clearTimeout(timer);
  }, [syncJob.finished?.id]);

  async function handleSync() {
    if (!syncJob.ready || !syncCooldownReady || syncing || syncCooldown > 0) return;
    setSyncMsg(null); setError(null);
    try {
      await Promise.all([setSyncCooldown(30), syncJob.start()]);
    } catch (err) {
      if (err instanceof ApiError && err.retryAfterSeconds > 0) await setSyncCooldown(err.retryAfterSeconds);
      setError(err instanceof Error ? err.message : "Could not start Sync. Checking server status before retrying.");
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

  function handleInspectFriend(entry: LeaderboardEntry) {
    setFriendDash(null); setRecentSolvesList([]); setProfileError("");
    setInspectedFriend(entry); setModalTab("overview");
  }
  useEffect(() => {
    if (!inspectedFriend) return;
    let cancelled = false;
    setLoadingFriendDash(true); setLoadingRecentSolves(true); setProfileError("");
    setRecentSolvesList([]);
    Promise.all([api.dashboard(inspectedFriend.id), api.recentSolves(inspectedFriend.id, 10)]).then(([profile, solves]) => {
      if (!cancelled) { setFriendDash(profile); setRecentSolvesList(solves); }
    }).catch(() => {
      if (!cancelled) { setFriendDash(null); setProfileError("Could not load this profile. Close and reopen it to retry."); }
    }).finally(() => {
      if (!cancelled) { setLoadingFriendDash(false); setLoadingRecentSolves(false); }
    });
    return () => { cancelled = true; };
  }, [inspectedFriend?.id]);

  function handleCopyCode(code: string) {
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  }

  if (error && !dash) return <div className="error-banner">{error}</div>;
  if (!dash) return <div className="centered muted" role="status">Loading your workspace…</div>;

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
      <div className="profile-bar" id="overview">
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
            disabled={!syncJob.ready || !syncCooldownReady || syncing || syncCooldown > 0}
            title="Sync your linked accounts; friends refresh automatically"
          >
            <img
              src={assetUrl("sync.png")}
              alt=""
              className={`sync-btn-icon ${syncing ? "spinning" : ""}`}
            />
            <span>{syncJob.submitting ? "Starting…" : syncing ? "Syncing…" : !syncJob.ready || !syncCooldownReady ? "Sync…" : syncCooldown > 0 ? `Sync (${syncCooldown}s)` : "Sync"}</span>
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
            <img src={assetUrl("streak_fire.png")} alt="🔥" className="toast-flame-img" />
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
      <div className="hero-card workspace-summary">
        <div className="streak-hero">
          <img src="/main_fire.png" alt="🔥" className="hero-flame-img" />
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
          <span className="diff-pill total">CF {dash.codeforces_count || 0}</span>
          <span className="diff-pill total">Total {dash.easy_count + dash.medium_count + dash.hard_count + (dash.codeforces_count || 0)}</span>
        </div>
      </div>



      <section className="workspace-week" aria-labelledby="week-title">
        <div className="section-header"><h2 id="week-title">Your last seven days</h2><span className="muted small">{dash.last_7_days.reduce((total, d) => total + d.problems_solved, 0)} activities</span></div>
        <div className="workspace-week-chart">{dash.last_7_days.map((day, index) => <div key={day.date} title={`${day.date}: ${day.problems_solved} activities`}>
          <span>{day.problems_solved}</span><div className="workspace-bar-track"><div style={{height: `${Math.max(3, day.problems_solved / maxDay * 100)}%`}} className={day.problems_solved ? "is-active" : ""} /></div>
          <span>{dayLabels[index]}</span></div>)}</div>
      </section>
      <section className="section workspace-leaderboard" id="leaderboards" aria-label="Leaderboards and groups">
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
        <div className="tab-bar-container" id="groups">
          {showGlobalLeaderboard(dash) && (
            <button
              className={`tab-btn ${selectedTab === "global" ? "active" : ""}`}
              onClick={() => changeTab("global")}
              title="Global Leaderboard (All platform users)"
            >
              🌐 Global
            </button>
          )}
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
                <img src={assetUrl("streak_fire.png")} alt="🔥" className="sort-fire-icon" /> Streak
              </button>
            </div>
          </div>

          <div className="sort-right-group">
            {(() => {
              const otherMembers = board?.entries?.filter((e) => e.id !== userId) || [];
              const unKudosed = otherMembers.filter((e) => !e.has_kudosed);
              const isAllKudosed = otherMembers.length > 0 && unKudosed.length === 0;
              return (
                <button
                  type="button"
                  className={`kudos-all-btn ${isAllKudosed ? "active" : ""}`}
                  onClick={handleKudosAll}
                  disabled={kudosAllBusy || isAllKudosed}
                  title={
                    isAllKudosed
                      ? "All members on this leaderboard have been kudosed today! 🙌"
                      : "Give kudos to all members on this leaderboard!"
                  }
                >
                  {kudosAllBusy
                    ? "Sending…"
                    : isAllKudosed
                    ? "🙌 All Kudosed"
                    : "👏 Kudos All"}
                </button>
              );
            })()}
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

        {activeGroup?.creator_id === userId && activeGroup.members.some(member => member.id !== userId) && <div className="group-transfer-row">
          <select aria-label="New group owner" value={transferTarget} onChange={event => setTransferTarget(event.target.value)}><option value="">Choose a new owner</option>{activeGroup.members.filter(member => member.id !== userId).map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</select>
          <button type="button" className="chip-btn" disabled={!transferTarget || transferBusy} onClick={handleTransferGroup}>{transferBusy ? "Transferring…" : "Transfer ownership"}</button>
        </div>}

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
                      <span className="streak-mini">
                        <img src={assetUrl("streak_fire.png")} alt="🔥" className="streak-mini-fire" />
                        {e.current_streak}d
                      </span>
                      <span className="solves-badge" title="Questions solved this week">
                        📝{e.weekly_total}
                      </span>
                      <span
                        className="points-badge"
                        title={`Easy: ${e.easy_count} | Medium: ${e.medium_count} | Hard: ${e.hard_count}`}
                      >
                        ⭐{formatPoints(e.points, "•••")}
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
          {!board && !boardLoading && <li className="workspace-board-empty">Leaderboard is temporarily unavailable. Use Sync to retry.</li>}
          {board && board.entries.length === 0 && <li className="workspace-board-empty">No members to show yet. Create or join a group to get started.</li>}
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
      </section>
      <section className="workspace-solves" id="activity" aria-labelledby="solves-title">
        <div className="section-header"><h2 id="solves-title">Your recent solves</h2><span className="web-feature-tag">Points breakdown</span></div>
        <p className="workspace-section-note">Select a solve to see how its points add up.</p>
        {ownSolvesLoading ? <p className="muted" role="status">Loading recent solves…</p> : ownSolvesError ? <p className="muted">Recent solves couldn't load. Use Sync to try again.</p> : ownSolves.length ? <ul className="workspace-solve-list">{ownSolves.map(solve => <li key={solve.title_slug}>
          <button onClick={() => setSelectedSolveBreakdown(solve)}><span><strong>{solve.title}</strong><small>{solve.relative_time}</small></span><span className="workspace-solve-score">+{formatPoints(solve.points_earned ?? 0)} pts <span aria-hidden="true">↗</span></span></button>
        </li>)}</ul> : <p className="muted">Your synced solves will appear here. Solve a problem on LeetCode, then select Sync.</p>}
      </section>
      <section className="workspace-community" aria-labelledby="community-title">
        <div className="section-header"><h2 id="community-title">Around the community</h2><span className="web-live-dot" /></div>
        {activityFeed.length ? <ul className="workspace-community-list">{activityFeed.slice(0, 5).map(item => <li key={`${item.user_id}-${item.title_slug}-${item.solved_at}`}>
          <a href={item.problem_url || item.leetcode_url} target="_blank" rel="noreferrer"><strong>{item.user_name}</strong><span>solved {item.title}</span><small>{item.platform === "codeforces" ? "Codeforces" : "LeetCode"} · {item.relative_time} ↗</small></a>
        </li>)}</ul> : <p className="muted">New community solves will show up here.</p>}
      </section>

      {/* Inspect Friend Modal */}
      {inspectedFriend && (
        <div className="modal-overlay" onClick={() => setInspectedFriend(null)}>
          <div className="modal-content profile-stats-modal" onClick={(e) => e.stopPropagation()}>
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
                {inspectedFriend.codeforces_username && <a className="profile-handle" href={`https://codeforces.com/profile/${encodeURIComponent(inspectedFriend.codeforces_username)}`} target="_blank" rel="noreferrer">CF @{inspectedFriend.codeforces_username} ↗</a>}
              </div>
            </div>

            <div className="modal-streak-box">
              <img src="/main_fire.png" alt="🔥" className="modal-flame-img" />
              <span className="modal-streak-count">{friendDash ? `${friendDash.current_streak} Day Streak` : "…"}</span>
              <span className="modal-points-tag">⭐ {formatPoints(friendDash?.points ?? inspectedFriend.points)} pts</span>
            </div>
            {profileError && <p className="tiny error-banner" role="alert">{profileError}</p>}

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
                {friendDash ? <>
                  <div className="section-title text-center mb-1">QUESTIONS SOLVED</div>
                  <div className="stat-row">
                    <Stat label="Today" value={friendDash.today_count} />
                    <Stat label="This Week" value={friendDash.weekly_total} />
                    <Stat label="This Month" value={friendDash.monthly_total} />
                  </div>
                  <div className="diff-pills">
                    <span className="diff-pill easy">Easy {friendDash.easy_count}</span>
                    <span className="diff-pill medium">Med {friendDash.medium_count}</span>
                    <span className="diff-pill hard">Hard {friendDash.hard_count}</span>
                    <span className="diff-pill total">CF {friendDash.codeforces_count || 0}</span>
                    <span className="diff-pill total">Total {friendDash.easy_count + friendDash.medium_count + friendDash.hard_count + (friendDash.codeforces_count || 0)}</span>
                  </div>
                </> : <p className="tiny muted" role="status">{loadingFriendDash ? "Loading profile metrics…" : "Profile metrics are unavailable."}</p>}

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
                                title={`${d.date}: ${solved} activit${solved === 1 ? "y" : "ies"}`}
                              />
                            </div>
                            <span className="profile-heat-day">{new Date(`${d.date}T12:00:00`).toLocaleDateString(undefined, { weekday: "short" })}</span>
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
                  <div className="centered muted tiny py-3">{profileError ? "Solves are unavailable." : "No recent solves recorded yet."}</div>
                ) : (
                  <ul className="recent-solves-list">
                    {recentSolvesList.map((s, idx) => {
                      const problemUrl = s.problem_url || s.leetcode_url || `https://leetcode.com/problems/${s.title_slug}`;
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
                              <small className="solve-platform">{s.platform === "codeforces" ? "Codeforces" : "LeetCode"}</small>
                            </span>
                          </div>
                          <a
                            href={problemUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="solve-external-link"
                            onClick={(e) => e.stopPropagation()}
                            title={`Open on ${s.platform === "codeforces" ? "Codeforces" : "LeetCode"}`}
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
                            ⭐ {formatPoints(s.points_earned ?? s.breakdown?.points_earned ?? 0)} pts
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
          <div className="modal-content settings-modal" role="dialog" aria-modal="true" aria-labelledby="account-settings-title" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 id="account-settings-title">Account Settings</h3>
              <button
                className="modal-close"
                onClick={() => setShowSettings(false)}
                title="Close settings"
              >
                ✕
              </button>
            </div>

            <div className="settings-body">
            {settingsMsg && <div className="settings-msg-banner">{settingsMsg}</div>}

            {/* Profile Summary Card */}
            <div className="settings-user-card">
              <div className="settings-user-left">
                {dash.avatar_url ? (
                  <img src={dash.avatar_url} alt={dash.name} className="settings-avatar" />
                ) : (
                  <div className="settings-avatar-placeholder">
                    {dash.name ? dash.name[0].toUpperCase() : "U"}
                  </div>
                )}
                <div className="settings-user-meta">
                  <span className="settings-user-name">{dash.name}</span>
                  <a
                    href={`https://leetcode.com/u/${dash.leetcode_username}/`}
                    target="_blank"
                    rel="noreferrer"
                    className="settings-user-handle"
                    title="View LeetCode Profile"
                  >
                    @{dash.leetcode_username} ↗
                  </a>
                </div>
              </div>
              <button
                type="button"
                className="settings-logout-btn"
                onClick={() => {
                  setShowSettings(false);
                  onResetUser();
                }}
                title="Log Out of this device"
              >
                🚪 Log Out
              </button>
            </div>

            {/* Section: PREFERENCES */}
            <div className="settings-section">
              <div className="settings-section-title">PREFERENCES</div>
              <div className="settings-card">
                <div className="settings-row">
                  <div className="settings-row-text">
                    <span className="settings-row-label">Show Global leaderboard</span>
                    <span className="settings-row-caption">
                      {showGlobalLeaderboard(dash)
                        ? "Shown on your home page; everyone participates"
                        : "Hidden here; you still participate"}
                    </span>
                  </div>
                  <label
                    className="settings-switch"
                    title={
                      showGlobalLeaderboard(dash)
                        ? "Hide Global leaderboard on your home page"
                        : "Show Global leaderboard on your home page"
                    }
                  >
                    <input
                      type="checkbox"
                      checked={showGlobalLeaderboard(dash)}
                      onChange={handleToggleGlobalLeaderboard}
                      disabled={togglingLeaderboard}
                    />
                    <span className="settings-slider" />
                  </label>
                </div>
              </div>
            </div>

            {/* Section: LEETCODE ACCOUNT */}
            <div className="settings-section">
              <div className="settings-section-title">LEETCODE ACCOUNT</div>
              <div className="settings-card">
                <form onSubmit={handleUpdateUsername} className="settings-username-form">
                  <div className="settings-input-wrapper">
                    <span className="settings-input-prefix">@</span>
                    <input
                      aria-label="LeetCode username"
                      value={newLeetcodeUsername}
                      onChange={(e) => setNewLeetcodeUsername(e.target.value)}
                      placeholder="Username"
                      className="settings-text-input"
                      required
                    />
                    <button
                      type="submit"
                      className="settings-action-btn"
                      disabled={
                        updatingUsername ||
                        !newLeetcodeUsername.trim() ||
                        newLeetcodeUsername.trim() === dash.leetcode_username
                      }
                    >
                      {updatingUsername ? "Saving…" : "Update"}
                    </button>
                  </div>
                  <span className="settings-input-hint">
                    A different handle replaces LeetCode history and retains Codeforces credit. Case-only edits keep history.
                  </span>
                </form>
                <button
                  type="button"
                  className="username-help-link-btn"
                  onClick={() => setShowUsernameHelpModal(true)}
                >
                  💡 Need help finding your LeetCode username?
                </button>
              </div>
            </div>

            <div className="settings-section">
              <div className="settings-section-title">CODEFORCES ACCOUNT</div>
              <div className="settings-card">
                <form onSubmit={handleUpdateCodeforces} className="settings-username-form">
                  <div className="settings-input-wrapper">
                    <span className="settings-input-prefix">@</span>
                    <input aria-label="Codeforces username" value={newCodeforcesUsername} onChange={e => setNewCodeforcesUsername(e.target.value)} placeholder={dash.codeforces_username || "Codeforces handle"} className="settings-text-input" maxLength={24} required />
                    <button type="submit" className="settings-action-btn" disabled={updatingCodeforces || !newCodeforcesUsername.trim()}>{updatingCodeforces ? "Connecting…" : dash.codeforces_username ? "Update" : "Connect"}</button>
                  </div>
                  <span className="settings-input-hint">{dash.codeforces_username ? `Connected: @${dash.codeforces_username}. ` : ""}Public accepted solves sync automatically with your points and streak.</span>
                  {dash.codeforces_username && <span className="settings-input-hint" role="status">{dash.codeforces_sync_error || (dash.codeforces_last_sync ? `Last synced ${new Date(dash.codeforces_last_sync + (/Z|[+-]\d\d:\d\d$/.test(dash.codeforces_last_sync) ? "" : "+05:30")).toLocaleString()}` : "Importing public history… Scores will update automatically.")}</span>}
                </form>
                <a className="username-help-link-btn" href="https://codeforces.com/" target="_blank" rel="noreferrer">Open Codeforces ↗</a>
              </div>
            </div>

            <section className="settings-section" aria-label="Account security">
              <div className="settings-section-title">Security</div>
              <div className="settings-card">
                <form className="settings-security-form" onSubmit={handleChangePassword}>
                  <label className="settings-security-label">Current password<div className="settings-input-wrapper"><input className="settings-text-input" type="password" autoComplete="current-password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} required maxLength={100} /></div></label>
                  <label className="settings-security-label">New password<div className="settings-input-wrapper"><input className="settings-text-input" type="password" autoComplete="new-password" value={changedPassword} onChange={event => setChangedPassword(event.target.value)} required minLength={15} maxLength={100} placeholder="At least 15 characters" /></div></label>
                  <button className="chip-btn settings-action-btn" type="submit" disabled={securityBusy}>{securityBusy ? "Please wait…" : "Change password"}</button>
                </form>
                <span className="settings-input-hint">Changing your password signs out other sessions. Passwords stay only in this open form.</span>
                <button type="button" className="chip-btn" disabled={securityBusy} onClick={handleRevokeSessions}>Sign out all devices</button>
              </div>
            </section>

            {/* Section: DANGER ZONE */}
            <div className="settings-section danger-section">
              <div className="settings-section-title danger-label">DANGER ZONE</div>
              <div className="settings-card danger-card">
                <div className="settings-row">
                  <div className="settings-row-text">
                    <span className="settings-row-label danger-text">Delete Account</span>
                    <span className="settings-row-caption">
                      Permanently wipe streaks and solve history
                    </span>
                  </div>
                  <button
                    type="button"
                    className="settings-delete-btn"
                    onClick={() => {
                      setShowSettings(false);
                      setDeletePassword("");
                      setDeleteError(null);
                      setShowDeleteModal(true);
                    }}
                  >
                    Delete…
                  </button>
                </div>
              </div>
            </div>

            {/* Section: ABOUT & LEGAL */}
            <div className="settings-legal-footer">
              <div className="settings-legal-links">
                <a
                  href="https://codestreak-api.onrender.com/privacy"
                  target="_blank"
                  rel="noreferrer"
                >
                  Privacy Policy ↗
                </a>
                <span>•</span>
                <a
                  href="https://codestreak-api.onrender.com/terms"
                  target="_blank"
                  rel="noreferrer"
                >
                  Terms &amp; EULA ↗
                </a>
                <span>•</span>
                <a
                  href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub ↗
                </a>
              </div>
              <p className="settings-legal-disclaimer">
                Independent open-source project. Not affiliated with LeetCode LLC.
              </p>
            </div>
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
                <img src={assetUrl("upi_qr.png")} alt="UPI QR Code" className="upi-qr-img" />
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

      {/* LeetCode Username Guide Modal */}
      {showUsernameHelpModal && (
        <LeetcodeUsernameHelpModal onClose={() => setShowUsernameHelpModal(false)} />
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
                  selectedSolveBreakdown.problem_url || selectedSolveBreakdown.leetcode_url ||
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

            <p className="tiny muted">Source: {selectedSolveBreakdown.platform === "codeforces" ? "Codeforces" : "LeetCode"}{selectedSolveBreakdown.source_handle ? ` · @${selectedSolveBreakdown.source_handle}` : ""}{selectedSolveBreakdown.source_submission_id ? ` · submission ${selectedSolveBreakdown.source_submission_id}` : ""}</p>
            {selectedSolveBreakdown.first_solve_verified === false && <p className="tiny muted">The first-solve date is unproved. This question does not add a streak day.</p>}
            {selectedSolveBreakdown.breakdown?.score_state === "legacy_protected" && <p className="tiny muted">Existing legacy credit is protected because its original bonus split is uncertain.</p>}
            {selectedSolveBreakdown.breakdown?.score_state === "metadata_missing" && <p className="tiny muted">Question metadata is incomplete. Existing credit is retained until it can be reconciled.</p>}
            {selectedSolveBreakdown.breakdown?.score_state === "history_review" && <p className="tiny muted">This question is missing from the latest public history. Its credit is retained for review.</p>}
            <div className="breakdown-card">
              <div className="breakdown-card-header"><span className="card-label">Credited points</span></div>
              {selectedSolveBreakdown.breakdown?.base_award === undefined ? <p className="tiny muted">Detailed credit is unavailable for this entry.</p> : <>
                <div className="breakdown-row"><span className="row-label">Base award:</span><span className="row-val">{formatPoints(selectedSolveBreakdown.breakdown.base_award)} pts</span></div>
                <div className="breakdown-row"><span className="row-label">Retained daily awards:</span><span className="row-val text-amber">{formatPoints(selectedSolveBreakdown.breakdown.daily_award ?? 0)} pts</span></div>
                <div className="breakdown-row"><span className="row-label">Revision awards:</span><span className="row-val text-violet">{formatPoints(selectedSolveBreakdown.breakdown.revision_award ?? 0)} pts</span></div>
                {(selectedSolveBreakdown.breakdown.legacy_credit ?? 0) > 0 && <div className="breakdown-row"><span className="row-label">Protected legacy credit:</span><span className="row-val">{formatPoints(selectedSolveBreakdown.breakdown.legacy_credit)} pts</span></div>}
                {(selectedSolveBreakdown.breakdown.base_award ?? 0) > 0 && <p className="tiny muted">Base includes its {selectedSolveBreakdown.breakdown.streak_multiplier ?? 1}× multiplier. Retained awards are not multiplied again.</p>}
              </>}
            </div>

            {/* Total Score Box */}
            <div className="breakdown-total-card">
              <div className="total-title-group">
                <div className="total-title">Total Points Earned</div>
                <div className="tiny muted">Total credit for this question</div>
              </div>
              <div className="total-score-badge">
                ⭐ {formatPoints(selectedSolveBreakdown.points_earned ?? selectedSolveBreakdown.breakdown?.points_earned ?? 0)} pts
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

function LeetcodeUsernameHelpModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content username-guide-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-heading">Finding Your LeetCode Username</h3>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            title="Close"
          >
            ✕
          </button>
        </div>

        <div className="username-guide-modal-body">
          <div className="guide-steps-list">
            <div className="guide-step-row">
              <span className="guide-step-badge">1</span>
              <span className="guide-step-text">
                Go to your profile on <strong>leetcode.com</strong> (click your avatar).
              </span>
            </div>
            <div className="guide-step-row">
              <span className="guide-step-badge">2</span>
              <span className="guide-step-text">
                Look directly <strong>below your display name</strong> for your unique handle:
              </span>
            </div>
          </div>

          <div className="username-guide-modal-img-wrapper">
            <img
              src={assetUrl("leetcode_username_guide.png")}
              alt="LeetCode Username Location Guide"
              className="username-guide-modal-img"
            />
          </div>

          <div className="guide-dos-donts-card">
            <div className="guide-check-item correct">
              <span className="guide-check-icon">✓</span>
              <div className="guide-check-content">
                <span className="guide-check-label">Enter Handle:</span>
                <code className="guide-code-highlight">leetcode_learner7</code>
              </div>
            </div>
            <div className="guide-check-item wrong">
              <span className="guide-check-icon">✕</span>
              <div className="guide-check-content">
                <span className="guide-check-label">Not Display Name:</span>
                <span className="guide-wrong-name">CodeNinja42</span>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer centered-footer">
          <button
            type="button"
            className="primary-btn center-btn"
            onClick={onClose}
            style={{ width: "auto", minWidth: "130px", padding: "8px 28px" }}
          >
            Got it 👍
          </button>
        </div>
      </div>
    </div>
  );
}

function PointsHelpModal({ onClose }: { onClose: () => void }) {
  const [section, setSection] = useState<string | null>(null);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") { event.stopPropagation(); onClose(); } };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const sections = [
    { id: "history", title: "History and score accuracy", hint: "First solves and retained historical credit", content: <>
      <p className="help-text">Question counts use verified first solves on LeetCode or Codeforces. Failed attempts and repeats do not add another solved question. The displayed streak temporarily includes imported activity while first-solve history is incomplete; that activity is not used to award points.</p>
      <p className="help-text">Some imported history has incomplete first-solve dates. Those questions can receive base-only historical credit while their dates remain excluded from scoring streaks and period counts.</p>
      <p className="help-text">Your credited points are locked. Sync adds points for new unique questions and eligible revisions without repricing old solves. New accounts receive their initial historical score once; filling gaps in that history does not award the same questions again. Changing to a different linked coding account replaces that platform's contribution.</p>
    </> },
    { id: "leetcode", title: "LeetCode points", hint: "Contest ratings and difficulty", content: <>
      <p className="help-text">Contest problems use ZeroTrac: <code>rating ÷ 100</code>. A 1500-rated problem earns 15 base points.</p>
      <p className="help-text">For other problems, Easy starts at <strong>8</strong>, Medium at <strong>15</strong>, and Hard at <strong>24</strong> points. Acceptance rate adjusts these bases; lower acceptance earns more.</p>
    </> },
    { id: "codeforces", title: "Codeforces points", hint: "Rating-based points · automatic sync", content: <>
      <p className="help-text">Base points = <code>8 + 0.012 × (rating − 800)</code>.</p>
      <ul className="help-bullet-list"><li>800 rating → 8 points</li><li>1400 → about 15 displayed points</li><li>1800 → 20 points</li><li>2200 → about 25 displayed points</li></ul>
      <p className="help-text">Connect your handle at signup or in Settings. Each unique, final accepted problem earns points once. Unrated accepted problems earn 0 base points. Only verified first solves count toward streaks. The scale is provisional, calibrated against similar LeetCode problems.</p>
    </> },
    { id: "daily", title: "Daily challenge bonus", hint: "Existing credit retained", content: <p className="help-text">A qualifying first solve of the current official LeetCode daily earns <strong>5 bonus points</strong>. An eligible streak can add up to 10% to these points. Imported history and repeats do not qualify. Live LeetCode first-solve verification is not available in this build; existing earned credit is retained.</p> },
    { id: "revision", title: "Revision points", hint: "Recurring seven-day cooldown", content: <p className="help-text">Earn <strong>2 revision points</strong> by solving a previously solved question again, at least seven days after its verified first solve or last rewarded revision. An eligible streak can add up to 10% to these points. Unrewarded attempts do not reset the clock. Initial history imports earn no revisions. Revisions never add a question, streak day or daily bonus.</p> },
    { id: "streak", title: "Streak multiplier", hint: "Up to +10%", content: <>
      <p className="help-text">The multiplier is <code>1 + 0.10 × min(streak days, 30) ÷ 30</code>, capped at <strong>1.10×</strong>.</p>
      <p className="help-text">Base awards use this multiplier. Previously earned daily and revision amounts are retained without multiplying them again. For example, a CF 1800 problem earns 20 base points, or 22 at the maximum multiplier.</p>
    </> },
  ];
  return <div className="modal-overlay points-help-overlay" onClick={onClose}>
    <div className="modal-content points-help-modal" role="dialog" aria-modal="true" aria-labelledby="points-help-title" onClick={event => event.stopPropagation()}>
      <div className="modal-header"><h3 id="points-help-title">How Points Work</h3><button type="button" className="modal-close" onClick={onClose} aria-label="Close scoring help">✕</button></div>
      <div className="help-section-list" aria-label="Scoring help topics">{sections.map(item => <div className="help-menu-item" key={item.id}>
        <button type="button" className="help-menu-toggle" id={`help-toggle-${item.id}`} aria-expanded={section === item.id} aria-controls={`help-content-${item.id}`} onClick={() => setSection(previous => previous === item.id ? null : item.id)}>
          <span><strong>{item.title}</strong><small>{item.hint}</small></span><span aria-hidden="true">{section === item.id ? "−" : "+"}</span>
        </button>
        <div id={`help-content-${item.id}`} role="region" aria-labelledby={`help-toggle-${item.id}`} hidden={section !== item.id} className="help-menu-content">{item.content}</div>
      </div>)}</div>
      <div className="modal-footer centered-footer"><button type="button" className="primary-btn center-btn" onClick={onClose}>Got it</button></div>
    </div>
  </div>;
}
