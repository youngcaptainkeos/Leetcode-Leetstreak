import React, { useEffect, useState, useRef } from "react";
import { api, GroupResponse } from "./lib/api";
import {
  STUDY_PLANS,
  StudyPlan,
  StudyQuestion,
  visiblePlans,
  planCounts,
  questionSolved,
  questionUrl,
  automaticQuestion,
  readStudyPlan,
  planFromLinks,
  fetchBundledOrCatalogPlan,
} from "./progressData";

interface ProgressProps {
  userId: number;
  username: string;
  groups: GroupResponse[];
}

interface FriendActivityItem {
  id: string;
  username: string;
  title: string;
  platform: string;
  timestamp: number;
  relativeTime: string;
  url: string;
}

export function WebsiteProgress({ userId, username, groups }: ProgressProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [followed, setFollowed] = useState<string[]>([]);
  const [hidden, setHidden] = useState<string[]>([]);
  const [manual, setManual] = useState<string[]>([]);
  const [customPlans, setCustomPlans] = useState<StudyPlan[]>([]);
  const [observedSlugs, setObservedSlugs] = useState<string[]>([]);
  const [cfHandle, setCfHandle] = useState<string | null>(null);
  const [cfObserved, setCfObserved] = useState<string[]>([]);
  const [selectedPlanSlug, setSelectedPlanSlug] = useState<string>("");

  // Search & Filter
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "done" | "remaining" | "external">("all");
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  // Add plan modal
  const [addOpen, setAddOpen] = useState(false);
  const [importMode, setImportMode] = useState<"link" | "paste">("link");
  const [planInput, setPlanInput] = useState("");
  const [pastedLinks, setPastedLinks] = useState("");
  const [importName, setImportName] = useState("");
  const [addingPlan, setAddingPlan] = useState(false);
  const [addError, setAddError] = useState("");

  // Friends activity
  const [friendActivity, setFriendActivity] = useState<FriendActivityItem[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(false);

  // Load progress and user solved questions on mount
  useEffect(() => {
    let active = true;
    setLoading(true);

    Promise.all([
      api.getProgress(userId).catch(() => null),
      api.codeforcesSolves(userId).catch(() => null),
      api.recentSolves(userId, 50).catch(() => []),
    ]).then(([progRes, cfRes, recentSolves]) => {
      if (!active) return;
      if (cfRes) {
        setCfHandle(cfRes.handle);
        setCfObserved(cfRes.slugs || []);
      }
      if (Array.isArray(recentSolves)) {
        setObservedSlugs(recentSolves.map((s) => s.title_slug));
      }

      if (progRes) {
        setFollowed(progRes.followed || []);
        setHidden(progRes.hidden || []);
        setManual(progRes.manual || []);
        const loadedCustom: StudyPlan[] = (progRes.custom_plans || [])
          .map(readStudyPlan)
          .filter((p: StudyPlan | null): p is StudyPlan => p !== null && !STUDY_PLANS.some((b) => b.slug === p.slug));
        setCustomPlans(loadedCustom);

        const allAvailable = visiblePlans([...STUDY_PLANS, ...loadedCustom], progRes.hidden || []);
        const initialSelected =
          (progRes.followed && progRes.followed.find((s: string) => allAvailable.some((p) => p.slug === s))) ||
          allAvailable[0]?.slug ||
          "";
        setSelectedPlanSlug(initialSelected);
      } else {
        setSelectedPlanSlug(STUDY_PLANS[0].slug);
      }
      setLoading(false);
    }).catch((err) => {
      if (active) {
        setError("Could not load study plans. Please try again.");
        setLoading(false);
      }
    });

    return () => { active = false; };
  }, [userId]);

  // Load friends recent activity
  useEffect(() => {
    let active = true;
    const friendUsers: { id: number; name: string; username: string }[] = [];
    for (const g of groups) {
      for (const m of g.members) {
        if (m.id !== userId && !friendUsers.some((u) => u.id === m.id)) {
          friendUsers.push({ id: m.id, name: m.name, username: m.leetcode_username });
        }
      }
    }

    if (friendUsers.length === 0) {
      setFriendActivity([]);
      return;
    }

    setLoadingFriends(true);
    Promise.all(
      friendUsers.slice(0, 10).map((f) =>
        api.recentSolves(f.id, 3).then((solves) =>
          solves.map((s) => ({
            id: `${f.id}-${s.title_slug}-${s.solved_at}`,
            username: f.name || f.username,
            title: s.title,
            platform: s.platform || "leetcode",
            timestamp: new Date(s.solved_at).getTime(),
            relativeTime: s.relative_time,
            url: s.problem_url || s.leetcode_url || `https://leetcode.com/problems/${s.title_slug}/`,
          }))
        ).catch(() => [] as FriendActivityItem[])
      )
    ).then((results) => {
      if (!active) return;
      const flat = results.flat().sort((a, b) => b.timestamp - a.timestamp).slice(0, 8);
      setFriendActivity(flat);
      setLoadingFriends(false);
    });

    return () => { active = false; };
  }, [groups, userId]);

  const library = visiblePlans([...STUDY_PLANS, ...customPlans], hidden);
  const activePlan = library.find((p) => p.slug === selectedPlanSlug) || library[0] || null;

  const solveState = {
    manual,
    observed: observedSlugs,
    codeforcesHandle: cfHandle,
    codeforcesObserved: cfObserved,
  };

  const currentCounts = activePlan ? planCounts(activePlan, solveState) : null;
  const isFollowing = activePlan ? followed.includes(activePlan.slug) : false;

  async function handleToggleFollow() {
    if (!activePlan) return;
    const nextFollowed = isFollowing
      ? followed.filter((s) => s !== activePlan.slug)
      : [...new Set([...followed, activePlan.slug])];
    setFollowed(nextFollowed);
    setNotice(isFollowing ? `Unfollowed ${activePlan.name}.` : `Following ${activePlan.name}.`);
    try {
      await api.updateProgress(userId, { followed: nextFollowed });
    } catch {
      // Offline fallback
    }
  }

  async function handleRemovePlan() {
    if (!activePlan) return;
    const slugToRemove = activePlan.slug;
    const remaining = library.filter((p) => p.slug !== slugToRemove);
    const nextCustom = customPlans.filter((p) => p.slug !== slugToRemove);
    const nextFollowed = followed.filter((s) => s !== slugToRemove);
    const isStarter = STUDY_PLANS.some((p) => p.slug === slugToRemove);
    const nextHidden = isStarter ? [...new Set([...hidden, slugToRemove])] : hidden;

    setCustomPlans(nextCustom);
    setFollowed(nextFollowed);
    setHidden(nextHidden);
    setSelectedPlanSlug(remaining[0]?.slug || "");
    setNotice(`${activePlan.name} removed.`);

    try {
      await api.deleteCustomPlan(userId, slugToRemove);
    } catch {
      // Offline fallback
    }
  }

  async function handleRestoreStarters() {
    setHidden([]);
    setSelectedPlanSlug(STUDY_PLANS[0].slug);
    setNotice("Starter plans restored.");
    try {
      await api.restoreStarters(userId);
    } catch {}
  }

  async function handleToggleManual(titleSlug: string) {
    const nextManual = manual.includes(titleSlug)
      ? manual.filter((s) => s !== titleSlug)
      : [...manual, titleSlug];
    setManual(nextManual);
    setNotice("External item completion saved.");
    try {
      await api.updateProgress(userId, { manual: nextManual });
    } catch {}
  }

  async function handleAddPlanSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (addingPlan) return;
    setAddError("");
    setAddingPlan(true);

    try {
      let newPlan: StudyPlan;
      if (importMode === "paste") {
        newPlan = planFromLinks(pastedLinks, importName);
      } else {
        newPlan = fetchBundledOrCatalogPlan(planInput);
      }

      setCustomPlans((prev) => [...prev.filter((p) => p.slug !== newPlan.slug), newPlan]);
      setFollowed((prev) => [...new Set([...prev, newPlan.slug])]);
      setHidden((prev) => prev.filter((s) => s !== newPlan.slug));
      setSelectedPlanSlug(newPlan.slug);

      await api.saveCustomPlan(userId, newPlan);

      setPlanInput("");
      setPastedLinks("");
      setImportName("");
      setAddOpen(false);
      setNotice(`Added and followed ${newPlan.name}.`);
    } catch (err: any) {
      setAddError(err.message || "Could not add this plan. Please check the links or catalog.");
    } finally {
      setAddingPlan(false);
    }
  }

  if (loading) {
    return (
      <div className="web-progress-container">
        <div className="web-progress-loading">Loading your study plans and progress…</div>
      </div>
    );
  }

  return (
    <div className="web-progress-container" id="progress">
      {/* Friends Activity */}
      {friendActivity.length > 0 && (
        <section className="web-friends-activity" aria-labelledby="friends-activity-title">
          <div className="web-progress-section-header">
            <h3 id="friends-activity-title">What are my friends up to?</h3>
            <span className="web-friends-subtitle">Recent activity from your groups</span>
          </div>
          <div className="web-friends-feed">
            {friendActivity.map((item) => (
              <div key={item.id} className="web-friend-item">
                <span className="web-friend-avatar">🧑‍💻</span>
                <div className="web-friend-details">
                  <span className="web-friend-name">{item.username}</span> solved{" "}
                  <a href={item.url} target="_blank" rel="noreferrer" className="web-friend-solve-link">
                    {item.title}
                  </a>
                  <span className="web-friend-platform-badge">{item.platform}</span>
                </div>
                <span className="web-friend-time">{item.relativeTime}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Study Plans Header */}
      <div className="web-progress-header">
        <div>
          <h2>Study Plans & Playlists</h2>
          <p className="web-progress-subtitle">
            Curated sheets, topic playlists, and custom question collections saved to your account.
          </p>
        </div>
        <div className="web-progress-actions">
          {hidden.length > 0 && (
            <button type="button" className="chip-btn" onClick={handleRestoreStarters}>
              Restore Starters
            </button>
          )}
          <button
            type="button"
            className="chip-btn primary"
            onClick={() => {
              setAddOpen(!addOpen);
              setAddError("");
            }}
          >
            {addOpen ? "Close" : "+ Add Plan"}
          </button>
        </div>
      </div>

      {notice && <div className="web-progress-notice">{notice}</div>}
      {error && <div className="web-progress-error">{error}</div>}

      {/* Add Plan Modal / Form */}
      {addOpen && (
        <div className="web-add-plan-box">
          <div className="web-add-plan-tabs">
            <button
              type="button"
              className={`chip-btn ${importMode === "link" ? "active" : ""}`}
              onClick={() => setImportMode("link")}
            >
              Catalog & Slugs
            </button>
            <button
              type="button"
              className={`chip-btn ${importMode === "paste" ? "active" : ""}`}
              onClick={() => setImportMode("paste")}
            >
              Paste Question Links
            </button>
          </div>

          <form onSubmit={handleAddPlanSubmit} className="web-add-plan-form">
            {importMode === "link" ? (
              <>
                <label htmlFor="plan-link-input">Study Plan Slug or Link</label>
                <input
                  id="plan-link-input"
                  type="text"
                  placeholder="e.g. leetcode-75, top-sql-50, or strivers-a2z"
                  value={planInput}
                  onChange={(e) => setPlanInput(e.target.value)}
                  disabled={addingPlan}
                  required
                />
                <p className="web-form-help">
                  Enter an official LeetCode study plan slug (like <code>leetcode-75</code>) or Striver's sheet.
                </p>
              </>
            ) : (
              <>
                <label htmlFor="playlist-name-input">Playlist Name</label>
                <input
                  id="playlist-name-input"
                  type="text"
                  placeholder="e.g. Dynamic Programming Favorites"
                  value={importName}
                  onChange={(e) => setImportName(e.target.value)}
                  disabled={addingPlan}
                  required
                />
                <label htmlFor="playlist-links-input">Question Links (one per line or space-separated)</label>
                <textarea
                  id="playlist-links-input"
                  placeholder="https://leetcode.com/problems/two-sum/&#10;https://codeforces.com/problemset/problem/4/A"
                  value={pastedLinks}
                  onChange={(e) => setPastedLinks(e.target.value)}
                  disabled={addingPlan}
                  rows={4}
                  required
                />
                <p className="web-form-help">
                  Paste LeetCode, Codeforces, or external problem URLs.
                </p>
              </>
            )}

            {addError && <div className="web-form-error">{addError}</div>}

            <div className="web-form-buttons">
              <button type="submit" className="web-button web-button-primary" disabled={addingPlan}>
                {addingPlan ? "Saving Plan…" : "Save to Account"}
              </button>
              <button type="button" className="web-button web-button-secondary" onClick={() => setAddOpen(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Plan Selection Cards */}
      <div className="web-plan-cards-scroll">
        {library.map((p) => {
          const counts = planCounts(p, solveState);
          const isSelected = p.slug === activePlan?.slug;
          return (
            <div
              key={p.slug}
              className={`web-plan-card ${isSelected ? "selected" : ""}`}
              onClick={() => setSelectedPlanSlug(p.slug)}
              tabIndex={0}
              role="button"
              aria-pressed={isSelected}
            >
              <div className="web-plan-card-top">
                <span className="web-plan-card-title">{p.name}</span>
                {followed.includes(p.slug) && <span className="web-plan-followed-pill">Following</span>}
              </div>
              <div className="web-plan-progress-bar">
                <div className="web-plan-progress-fill" style={{ width: `${counts.percent}%` }} />
              </div>
              <div className="web-plan-card-bottom">
                <span>{counts.done} / {counts.total} solved</span>
                <span className="web-plan-percent">{counts.percent}%</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Plan Detail View */}
      {activePlan && currentCounts && (
        <div className="web-active-plan-detail">
          <div className="web-active-plan-header">
            <div>
              <h3>{activePlan.name}</h3>
              <div className="web-active-plan-stats">
                <span>{currentCounts.done} of {currentCounts.total} questions completed ({currentCounts.percent}%)</span>
                {currentCounts.next && (
                  <span className="web-next-up">
                    Next: <a href={questionUrl(currentCounts.next)} target="_blank" rel="noreferrer">{currentCounts.next.title} ↗</a>
                  </span>
                )}
              </div>
            </div>
            <div className="web-active-plan-actions">
              <button
                type="button"
                className={`chip-btn ${isFollowing ? "active" : ""}`}
                onClick={handleToggleFollow}
              >
                {isFollowing ? "✓ Following" : "+ Follow"}
              </button>
              <button type="button" className="chip-btn danger" onClick={handleRemovePlan}>
                Remove Plan
              </button>
            </div>
          </div>

          {/* Filter and Search Bar */}
          <div className="web-filter-bar">
            <input
              type="text"
              placeholder="Search questions in this plan…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="web-search-input"
            />
            <div className="web-filter-chips">
              {(["all", "done", "remaining", "external"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`chip-btn ${filter === mode ? "active" : ""}`}
                  onClick={() => setFilter(mode)}
                >
                  {mode === "all" ? "All" : mode === "done" ? "Solved" : mode === "remaining" ? "To Do" : "External"}
                </button>
              ))}
            </div>
          </div>

          {/* Subgroups & Question List */}
          <div className="web-question-groups">
            {activePlan.planSubGroups.map((group) => {
              const filteredQuestions = group.questions.filter((q) => {
                const matchesSearch = q.title.toLowerCase().includes(search.toLowerCase());
                if (!matchesSearch) return false;
                const isSolved = questionSolved(q, solveState);
                const isAuto = automaticQuestion(q, cfHandle);
                if (filter === "done") return isSolved;
                if (filter === "remaining") return !isSolved;
                if (filter === "external") return !isAuto;
                return true;
              });

              if (filteredQuestions.length === 0) return null;

              const isCollapsed = collapsedGroups[group.name] ?? false;
              const solvedCount = group.questions.filter((q) => questionSolved(q, solveState)).length;

              return (
                <div key={group.name} className="web-subgroup">
                  <div
                    className="web-subgroup-header"
                    onClick={() =>
                      setCollapsedGroups((prev) => ({ ...prev, [group.name]: !isCollapsed }))
                    }
                  >
                    <span className="web-subgroup-toggle">{isCollapsed ? "▶" : "▼"}</span>
                    <span className="web-subgroup-title">{group.name}</span>
                    <span className="web-subgroup-badge">{solvedCount} / {group.questions.length}</span>
                  </div>

                  {!isCollapsed && (
                    <div className="web-question-list">
                      {filteredQuestions.map((q) => {
                        const isSolved = questionSolved(q, solveState);
                        const isAuto = automaticQuestion(q, cfHandle);

                        return (
                          <div key={q.titleSlug} className={`web-question-row ${isSolved ? "solved" : ""}`}>
                            <div className="web-question-left">
                              {isAuto ? (
                                <span className={`web-auto-check ${isSolved ? "checked" : ""}`} title={isSolved ? "Verified solved on coding platform" : "Not yet solved on platform"}>
                                  {isSolved ? "✓" : "○"}
                                </span>
                              ) : (
                                <input
                                  type="checkbox"
                                  className="web-manual-checkbox"
                                  checked={isSolved}
                                  onChange={() => handleToggleManual(q.titleSlug)}
                                  title="Check to mark external item completed"
                                />
                              )}
                              <a
                                href={questionUrl(q)}
                                target="_blank"
                                rel="noreferrer"
                                className="web-question-link"
                              >
                                {q.title}
                              </a>
                            </div>
                            <div className="web-question-right">
                              <span className={`web-diff-tag ${q.difficulty.toLowerCase()}`}>
                                {q.difficulty}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
