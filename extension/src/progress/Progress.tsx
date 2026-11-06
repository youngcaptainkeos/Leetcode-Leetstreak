import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { api, GroupResponse, GroupMember } from "../lib/api";
import { getStored, setStored } from "../storage";
import { STUDY_PLANS, PRACTICE_REFRESH, PracticeSnapshot, StudyPlan, Submission, dailySolved, fetchPractice, fetchFriendSubmissions, planCounts, progressKey, parsePlanInput, fetchStudyPlan, questionUrl, questionSolved, questionLeetcodeSlug, questionCodeforcesSlug, automaticQuestion, visiblePlans } from "./data";
import { fetchSolvedHistory, SolvedHistory } from "./history";
import { planFromLinks, requestImportAccess } from "./importer";
import { useAccountProgress } from "./accountSync";
import { PlanView, ProgressView, readProgressView, emptyPlanView } from "./view";
import "./Progress.css";

export function usePractice(username: string) {
  const [snapshot, setSnapshot] = useState<PracticeSnapshot | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const retry = () => setRefresh(n => n + 1);
  useEffect(() => {
    const update = () => retry();
    window.addEventListener(PRACTICE_REFRESH, update);
    window.addEventListener("online", update);
    const interval = window.setInterval(update, 60000);
    return () => { clearInterval(interval); window.removeEventListener(PRACTICE_REFRESH, update); window.removeEventListener("online", update); };
  }, []);
  useEffect(() => {
    let active = true;
    setSnapshot(null);
    setError("");
    if (!username) return;
    fetchPractice(username, refresh > 0).then(data => { if (active) setSnapshot(data); })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : "Could not refresh practice data."); });
    return () => { active = false; };
  }, [username, refresh]);
  return { snapshot, error, retry };
}

export function DailyReminder({ userId, username, snapshot, error, retry }: { userId: number; username: string; snapshot: PracticeSnapshot | null; error: string; retry: () => void }) {
  const [dismissed, setDismissed] = useState<string | null>(null);
  const daily = snapshot?.daily;
  const key = `codestreak_daily_dismissed_${userId}_${username.toLowerCase()}`;
  useEffect(() => {
    let active = true;
    getStored(key).then(value => { if (active) setDismissed(value || ""); });
    return () => { active = false; };
  }, [key]);
  useEffect(() => {
    if (snapshot && dailySolved(snapshot)) {
      setDismissed(snapshot.daily.date);
      void setStored(key, snapshot.daily.date);
    }
  }, [key, snapshot]);
  const slot = document.getElementById("daily-reminder-slot");
  if (error) {
    const message = <div className="practice-unavailable" role="status">Daily challenge check unavailable. <button onClick={retry}>Retry</button></div>;
    return slot ? createPortal(message, slot) : message;
  }
  // LeetCode's daily challenge resets at midnight UTC, independently of local time.
  if (dismissed === null || !snapshot || !daily || daily.date !== new Date().toISOString().slice(0, 10) || dailySolved(snapshot) || dismissed === daily.date) return null;
  const banner = <aside className="daily-practice-banner" role="status" aria-label="Daily challenge reminder">
    <span className="daily-practice-icon" aria-hidden="true">✦</span>
    <div><strong>Today's daily is waiting for you</strong><span>{daily.title}</span><a href={`https://leetcode.com/problems/${daily.slug}/`} target="_blank" rel="noreferrer">Solve today's challenge ↗</a><small>Checked against your recent public accepted submissions.</small></div>
    <button className="daily-practice-dismiss" aria-label="Dismiss reminder for today" title="Dismiss for today — stays closed when you reopen the extension" onClick={() => { setDismissed(daily.date); void setStored(key, daily.date); }}>×</button>
  </aside>;
  return slot ? createPortal(banner, slot) : banner;
}

export function ProgressPanel({ userId, username, snapshot, error, groups, active }: {
  userId: number; username: string; snapshot: PracticeSnapshot | null; error: string; groups: GroupResponse[]; active: boolean;
}) {
  const key = progressKey(userId, username);
  const { state, setState, status: planSyncStatus, mutate, retry: retryPlanSync } = useAccountProgress(userId, username);
  const [view, setView] = useState<ProgressView | null>(null);
  const selected = view?.selected || STUDY_PLANS[0].slug;
  const planView = view && Object.prototype.hasOwnProperty.call(view.plans, selected) ? view.plans[selected] : emptyPlanView();
  const showQuestions = planView.showQuestions;
  const expandedGroups = planView.expandedGroups;
  function updatePlanView(update: (previous: PlanView) => PlanView) {
    setView(previous => {
      if (!previous) return previous;
      const current = Object.prototype.hasOwnProperty.call(previous.plans, selected) ? previous.plans[selected] : emptyPlanView();
      const next = update(current);
      if (next.showQuestions === current.showQuestions && next.expandedGroups === current.expandedGroups) return previous;
      return { ...previous, plans: { ...previous.plans, [selected]: next } };
    });
  }
  function setShowQuestions(value: React.SetStateAction<boolean>) {
    updatePlanView(previous => ({ ...previous, showQuestions: typeof value === "function" ? value(previous.showQuestions) : value }));
  }
  function setExpandedGroups(value: React.SetStateAction<string[]>) {
    updatePlanView(previous => ({ ...previous, expandedGroups: typeof value === "function" ? value(previous.expandedGroups) : value }));
  }
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [notice, setNotice] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [planInput, setPlanInput] = useState("");
  const [importMode, setImportMode] = useState<"link" | "paste">("link");
  const [pastedLinks, setPastedLinks] = useState("");
  const [importName, setImportName] = useState("");
  const [importPreview, setImportPreview] = useState<StudyPlan | null>(null);
  const [addingPlan, setAddingPlan] = useState(false);
  const [planError, setPlanError] = useState("");
  const [historySyncing, setHistorySyncing] = useState(false);
  const [historyMessage, setHistoryMessage] = useState("");
  const [historyError, setHistoryError] = useState("");
  const importRequest = useRef(0);
  const historyRequest = useRef<AbortController | null>(null);
  const historyPromise = useRef<Promise<SolvedHistory | null> | null>(null);
  const stateRef = useRef(state);
  stateRef.current = state;
  useEffect(() => () => { importRequest.current++; historyRequest.current?.abort(); }, []);
  useEffect(() => {
    let active = true;
    getStored(`${key}_view`).then(savedView => {
      if (active) setView(readProgressView(savedView));
    });
    return () => { active = false; };
  }, [key]);
  useEffect(() => { if (view) void setStored(`${key}_view`, JSON.stringify(view)); }, [key, view]);
  const loaded = state !== null && view !== null;
  async function syncHistory(force = false): Promise<SolvedHistory | null> {
    const saved = stateRef.current;
    if (!force && saved?.lastFullSyncAt && Date.now() - saved.lastFullSyncAt < 15 * 60000) {
      return { slugs: saved.observed, syncedAt: saved.lastFullSyncAt };
    }
    if (historyPromise.current) return historyPromise.current;
    const controller = new AbortController();
    historyRequest.current = controller;
    setHistorySyncing(true); setHistoryError(""); setHistoryMessage("Syncing your solved history…");
    const task = (async () => {
      try {
        const result = await fetchSolvedHistory(username, (done, total) => {
          if (!controller.signal.aborted) setHistoryMessage(`Syncing solved history: ${done}/${total}`);
        }, controller.signal);
        if (controller.signal.aborted) return null;
        mutate("observe", { handle: username, slugs: result.slugs, syncedAt: result.syncedAt });
        setHistoryMessage(`${result.slugs.length} solved LeetCode questions synced.`);
        return result;
      } catch (err) {
        if (!controller.signal.aborted) {
          setHistoryMessage("");
          setHistoryError(err instanceof Error && err.name === "AbortError" ? "LeetCode took too long to respond. History will retry automatically." : err instanceof Error ? err.message : "Could not sync solved history. Your saved progress is unchanged.");
        }
        return null;
      } finally {
        if (!controller.signal.aborted) setHistorySyncing(false);
        if (historyRequest.current === controller) { historyRequest.current = null; historyPromise.current = null; }
      }
    })();
    historyPromise.current = task;
    return task;
  }
  useEffect(() => {
    if (!loaded) return;
    void syncHistory();
    const refresh = () => { void syncHistory(); };
    window.addEventListener(PRACTICE_REFRESH, refresh);
    window.addEventListener("online", refresh);
    window.addEventListener("focus", refresh);
    const interval = window.setInterval(refresh, 60000);
    return () => {
      clearInterval(interval);
      window.removeEventListener(PRACTICE_REFRESH, refresh);
      window.removeEventListener("online", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, [loaded, username]);
  useEffect(() => {
    if (!loaded || !snapshot) return;
    mutate("observe", { handle: username, slugs: snapshot.submissions.map(s => s.titleSlug) });
  }, [loaded, snapshot]);

  useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    const update = () => { void api.codeforcesSolves(userId).then(data => {
      if (!cancelled) setState(previous => previous ? { ...previous, codeforcesHandle: data.handle, codeforcesObserved: data.slugs, codeforcesSyncedAt: data.synced_at } : previous);
    }).catch(() => { /* Preserve saved completion while offline. */ }); };
    update();
    const interval = setInterval(update, 30000);
    window.addEventListener(PRACTICE_REFRESH, update);
    return () => { cancelled = true; clearInterval(interval); window.removeEventListener(PRACTICE_REFRESH, update); };
  }, [loaded, userId]);

  if (!state || !view) return <div className="centered muted">Loading your progress…</div>;
  const library = visiblePlans(state);
  const plan = library.find(p => p.slug === selected) || library[0] || null;
  const count = plan ? planCounts(plan, state) : null;
  const following = plan ? state.followed.includes(plan.slug) : false;
  function selectPlan(slug: string) {
    setView(previous => previous ? { ...previous, selected: slug } : previous);
    setSearch(""); setFilter("all"); setNotice("");
  }
  function closeImporter() {
    importRequest.current++;
    setAddingPlan(false); setAddOpen(false); setPlanError(""); setImportPreview(null);
  }
  async function handleAddPlan(event: React.FormEvent) {
    event.preventDefault();
    if (addingPlan) return;
    const request = ++importRequest.current;
    setPlanError(""); setAddingPlan(true);
    try {
      if (!importPreview) {
        let preview: StudyPlan;
        if (importMode === "paste") preview = planFromLinks(pastedLinks, importName);
        else {
          const parsed = parsePlanInput(planInput);
          const existing = [...STUDY_PLANS, ...(state?.customPlans || [])].find(p => p.slug === parsed.slug);
          if (!existing && parsed.source !== "leetcode") await requestImportAccess(parsed.url!);
          preview = existing || await fetchStudyPlan(planInput);
        }
        if (request === importRequest.current) setImportPreview(preview);
        return;
      }
      const imported = importPreview;
      const hasLeetCode = imported.planSubGroups.some(group => group.questions.some(q => questionLeetcodeSlug(q)));
      const history = hasLeetCode ? await syncHistory(true) : null;
      if (request !== importRequest.current) return;
      mutate("add", { plan: imported });
      selectPlan(imported.slug);
      setNotice(!hasLeetCode ? `Following ${imported.name}. External-item completion is saved with the plan.` : history ? `Following ${imported.name}. Progress synced with your solved history.` : `Following ${imported.name}. Saved solves are shown; older solves will appear when automatic LeetCode syncing succeeds.`);
      setPlanInput(""); setPastedLinks(""); setImportName(""); setImportPreview(null); setAddOpen(false);
    } catch (err) {
      if (request === importRequest.current) setPlanError(err instanceof Error ? err.message : "Could not add this study plan. Please try again.");
    } finally {
      if (request === importRequest.current) setAddingPlan(false);
    }
  }
  function handleRemovePlan() {
    if (!plan) return;
    const remaining = library.filter(p => p.slug !== plan.slug);
    mutate("remove", { slug: plan.slug });
    selectPlan(remaining[0]?.slug || "");
    setNotice(`${plan.name} removed. Your solved questions are kept if you add it again.`);
  }
  function restoreStarters() {
    mutate("restore", {});
    selectPlan(STUDY_PLANS[0].slug);
    setNotice("Starter plans restored. Your saved progress is still here.");
  }
  async function toggleFollow() {
    if (!plan) return;
    if (!following && plan.planSubGroups.some(group => group.questions.some(q => questionLeetcodeSlug(q)))) await syncHistory(true);
    mutate("follow", { slug: plan.slug, enabled: !following });
    setNotice(following ? `${plan.name} removed from following. Your progress is saved.` : `Following ${plan.name}. Your saved progress is applied.`);
  }
  function toggleExternalItem(slug: string) {
    const question = plan?.planSubGroups.flatMap(group => group.questions).find(q => q.titleSlug === slug);
    if (!question || automaticQuestion(question, state!)) return;
    mutate("manual", { slug, enabled: !state!.manual.includes(slug) });
    setNotice("External-item completion saved.");
  }
  const visibleGroups = plan?.planSubGroups.map(g => ({ ...g, questions: g.questions.filter(q =>
    q.title.toLowerCase().includes(search.toLowerCase()) && (filter === "all" || (filter === "external" ? !automaticQuestion(q, state) : filter === "done" ? questionSolved(q, state) : !questionSolved(q, state)))) })).filter(g => g.questions.length) || [];
  return <div className="progress-panel" id="progress-panel" role="tabpanel" aria-labelledby="progress-menu">
    {active && <FriendsActivity key={`${userId}-${username}`} userId={userId} groups={groups} />}
    <div className="section-header study-plans-heading"><h2 className="section-title">Study plans</h2><button className="chip-btn" aria-expanded={addOpen} aria-controls="add-study-plan" onClick={() => { if (addOpen) closeImporter(); else { setAddOpen(true); setPlanError(""); } }}>{addOpen ? "Close" : "+ Add plan"}</button></div>
    <div className="history-sync-row"><span role="status">{planSyncStatus}</span>{/unavailable|could not|full|not saved|removed/i.test(planSyncStatus) && <button className="chip-btn" onClick={retryPlanSync}>Retry save</button>}</div>
    <div className="history-sync-row"><span role="status">{historySyncing ? historyMessage : state.lastFullSyncAt ? `LeetCode history saved · ${new Date(state.lastFullSyncAt).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}` : "LeetCode history syncs automatically"}</span></div>
    {historyError && <p className="progress-error" role="status">{historyError} <a href="https://leetcode.com/" target="_blank" rel="noreferrer">Open LeetCode ↗</a></p>}
    {addOpen && <form className="plan-import-form" id="add-study-plan" onSubmit={handleAddPlan}>
      <div className="plan-import-modes" role="group" aria-label="Import method">
        <button type="button" className="chip-btn" aria-pressed={importMode === "link"} disabled={addingPlan} onClick={() => { setImportMode("link"); setImportPreview(null); setPlanError(""); }}>Scan a link</button>
        <button type="button" className="chip-btn" aria-pressed={importMode === "paste"} disabled={addingPlan} onClick={() => { setImportMode("paste"); setImportPreview(null); setPlanError(""); }}>Paste question links</button>
      </div>
      {importMode === "link" ? <>
        <label htmlFor="study-plan-link">Study-plan or playlist link</label>
        <input id="study-plan-link" type="text" value={planInput} onChange={e => { setPlanInput(e.target.value); setImportPreview(null); }} placeholder="Paste a public playlist link…" maxLength={1000} autoFocus aria-describedby="plan-import-help" disabled={addingPlan} />
        <p className="progress-note" id="plan-import-help">LeetCode plans, takeUforward sheets, Codeforces contests and filtered problemsets, or public pages with question links. Your browser may ask for access to the site you choose.</p>
      </> : <>
        <label htmlFor="import-plan-name">Plan name</label>
        <input id="import-plan-name" value={importName} maxLength={150} placeholder="My practice plan" disabled={addingPlan} onChange={e => { setImportName(e.target.value); setImportPreview(null); }} />
        <label htmlFor="import-question-links">Question links · one per line</label>
        <textarea id="import-question-links" value={pastedLinks} maxLength={200000} rows={5} placeholder={"Two Sum https://leetcode.com/problems/two-sum/\nhttps://codeforces.com/problemset/problem/4/A"} disabled={addingPlan} onChange={e => { setPastedLinks(e.target.value); setImportPreview(null); }} />
        <p className="progress-note">Use this for blocked or interactive pages. Include an optional question title before each link. LeetCode links sync automatically; other sites use saved checkboxes.</p>
      </>}
      {importPreview && <section className="plan-import-preview" aria-label="Review imported plan">
        <strong>{importPreview.name}</strong>
        <p className="progress-note">{importPreview.planSubGroups.reduce((n, group) => n + group.questions.length, 0)} questions · {importPreview.planSubGroups.length} sections. Review before adding: a page scan may find only the questions that page makes public.</p>
        <ul>{importPreview.planSubGroups.map(group => <li key={group.name}><b>{group.name}</b><ul>{group.questions.map(q => <li key={q.titleSlug}><a href={questionUrl(q)} target="_blank" rel="noreferrer">{q.title} ↗</a><small>{automaticQuestion(q, state) ? questionCodeforcesSlug(q) ? "Codeforces · automatic" : "LeetCode · automatic" : "External · checkbox"}</small></li>)}</ul></li>)}</ul>
      </section>}
      <div className="plan-import-actions"><button className="chip-btn" type="submit" disabled={addingPlan || (importMode === "link" ? !planInput.trim() : !pastedLinks.trim())}>{addingPlan ? importPreview ? "Adding & syncing…" : "Reading questions…" : importPreview ? "Add & follow" : importMode === "link" ? "Scan link" : "Review questions"}</button><button className="chip-btn" type="button" onClick={closeImporter}>Cancel</button></div>
      {planError && <p className="progress-error" role="alert">{planError}</p>}
    </form>}
    <div className="progress-notice" role="status" aria-live="polite">{notice}</div>
    {!library.length && <section className="plan-library-empty" aria-label="No study plans"><strong>Your next plan starts here</strong><p className="progress-note">Add a study plan or sheet, or bring back the three starter plans. Your saved solves are kept.</p><div className="plan-import-actions"><button className="chip-btn" onClick={() => setAddOpen(true)}>Add a plan</button><button className="chip-btn" onClick={restoreStarters}>Restore starter plans</button></div></section>}
    <div className="study-plan-list" id="study-plans" aria-label="Study plans">{library.map(p => { const c = planCounts(p, state); return <button key={p.slug} className={`study-plan-option ${p.slug === plan?.slug ? "selected" : ""}`} aria-pressed={p.slug === plan?.slug} onClick={() => selectPlan(p.slug)}>
      <span><strong>{p.name}</strong><small>{state.followed.includes(p.slug) ? "Following · " : ""}{c.done}/{c.total} {p.source && p.source !== "leetcode" ? "completed" : "solved"}</small></span><span className="plan-mini-meter" aria-hidden="true"><i style={{ width: `${c.percent}%` }} /></span><b>{c.percent}%</b>
    </button>; })}</div>
    {plan && count && <section className="study-plan-detail" aria-label={`${plan.name} progress`}>
      <div className="study-plan-top"><div><h3>{plan.name}</h3><a href={plan.sourceUrl || (plan.source === "external" ? questionUrl(plan.planSubGroups[0].questions[0]) : `https://leetcode.com/studyplan/${plan.slug}/`)} target="_blank" rel="noreferrer">View on {plan.source === "takeuforward" ? "takeUforward" : plan.source === "codeforces" ? "Codeforces" : plan.source === "external" ? "source site" : "LeetCode"} ↗</a></div><button className={`chip-btn ${following ? "is-following" : ""}`} aria-pressed={following} disabled={historySyncing && !following} onClick={toggleFollow}>{following ? "✓ Following" : "+ Follow plan"}</button></div>
      <div className="plan-progress-label"><strong>{count.done}<span> / {count.total} {plan.source && plan.source !== "leetcode" ? "completed" : "solved"}</span></strong><b>{count.percent}%</b></div>
      <div className="plan-progress-track" role="progressbar" aria-label={`${plan.name} completion`} aria-valuenow={count.done} aria-valuemin={0} aria-valuemax={count.total}><div style={{ width: `${count.percent}%` }} /></div>
      {count.next ? <a className="plan-continue" href={questionUrl(count.next)} target="_blank" rel="noreferrer"><span>{(automaticQuestion(count.next, state) ? questionCodeforcesSlug(count.next) ? state.codeforcesSyncedAt : state.lastFullSyncAt : true) ? "UP NEXT" : "NOT YET VERIFIED"}<strong>{count.next.title}</strong></span><span aria-hidden="true">↗</span></a> : <p className="plan-complete">{count.total ? "✦ Plan complete. Enjoy that milestone!" : "This plan has no items to track."}</p>}
      <p className="progress-note">{plan.source && plan.source !== "leetcode" ? `${plan.snapshotDate ? `Public list snapshot: ${plan.snapshotDate}. ` : ""}${count.automatic} linked problems sync automatically. The ${count.external} other items have external links and completion checkboxes.` : "Progress comes from your synced LeetCode solved history."} Progress is saved for this account and applied when you add a plan.</p>
      {error && <p className="progress-error" role="status">Automatic checking is unavailable. Your saved progress is still here.</p>}
      <div className="plan-question-controls"><button className="chip-btn" aria-expanded={showQuestions} aria-controls="plan-question-list" onClick={() => setShowQuestions(value => !value)}>{showQuestions ? "Hide questions ↑" : "Show questions ↓"}</button>{showQuestions && <button className="chip-btn" onClick={() => { const allOpen = visibleGroups.every(g => expandedGroups.includes(g.name)); setExpandedGroups(allOpen ? [] : visibleGroups.map(g => g.name)); }}>{visibleGroups.length > 0 && visibleGroups.every(g => expandedGroups.includes(g.name)) ? "Collapse all" : "Expand all"}</button>}<button className="chip-btn plan-remove" aria-label={`Remove ${plan.name} from your plans`} title="Remove plan; keep solved history" onClick={handleRemovePlan}>Remove plan</button></div>
      {showQuestions && <div id="plan-question-list"><div className="plan-tools"><input type="search" aria-label="Search plan questions" placeholder="Find a question…" value={search} onChange={e => { setSearch(e.target.value); if (e.target.value) setExpandedGroups(plan.planSubGroups.map(g => g.name)); }} /><select aria-label="Filter plan questions" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All questions</option><option value="todo">To do</option><option value="done">Completed</option>{count.external > 0 && <option value="external">External items</option>}</select></div>
      <div className="plan-question-groups">{visibleGroups.length ? visibleGroups.map(group => <details key={`${plan.slug}-${group.name}`} open={expandedGroups.includes(group.name)} onToggle={e => { const open = e.currentTarget.open; setExpandedGroups(previous => open ? previous.includes(group.name) ? previous : [...previous, group.name] : previous.includes(group.name) ? previous.filter(name => name !== group.name) : previous); }}>
        <summary>{group.name}<span>{group.questions.filter(q => questionSolved(q, state)).length}/{group.questions.length}</span></summary>
        <ul>{group.questions.map(q => <li key={q.titleSlug} className={questionSolved(q, state) ? "question-done" : ""}>
          {automaticQuestion(q, state) ? <span className={`question-sync-status ${questionSolved(q, state) ? "is-solved" : ""}`} role="img" aria-label={`${q.title}: ${questionSolved(q, state) ? questionCodeforcesSlug(q) ? "solved on Codeforces" : "solved on LeetCode" : "not found in synced solves"}`}>{questionSolved(q, state) ? "✓" : "○"}</span> : <input type="checkbox" checked={questionSolved(q, state)} aria-label={`${q.title}: completed externally`} onChange={() => toggleExternalItem(q.titleSlug)} />}
          <a href={questionUrl(q)} target="_blank" rel="noreferrer">{q.title}<small className={`question-difficulty ${q.difficulty.toLowerCase()}`}>{q.difficulty.toLowerCase()} · {automaticQuestion(q, state) ? questionSolved(q, state) ? "synced" : (questionCodeforcesSlug(q) ? state.codeforcesSyncedAt : state.lastFullSyncAt) ? "not solved" : "not verified" : "external item"}</small></a><span aria-hidden="true">↗</span>
        </li>)}</ul>
      </details>) : <p className="progress-note">No questions match this filter.</p>}</div></div>}
    </section>}
  </div>;
}

interface FriendSolve extends Submission { friend: GroupMember; platform?: string; problemUrl?: string }
function FriendsActivity({ userId, groups }: { userId: number; groups: GroupResponse[] }) {
  const friends = [...new Map(groups.flatMap(g => g.members).filter(m => m.id !== userId).map(m => [m.id, m])).values()];
  const signature = JSON.stringify(friends.map(f => [f.id, f.leetcode_username, f.codeforces_username]).sort());
  const [items, setItems] = useState<FriendSolve[]>([]);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const [filter, setFilter] = useState("all");
  useEffect(() => {
    const update = () => setRefresh(n => n + 1);
    window.addEventListener(PRACTICE_REFRESH, update);
    return () => window.removeEventListener(PRACTICE_REFRESH, update);
  }, []);
  useEffect(() => {
    let active = true;
    setItems([]); setFailed(0);
    if (!friends.length) { setBusy(false); return; }
    setBusy(true);
    // Bound concurrency so a large squad doesn't flood LeetCode with requests.
    const queue = [...friends];
    const results: FriendSolve[] = [];
    let failures = 0;
    async function worker() {
      while (queue.length && active) {
        const friend = queue.shift()!;
        try {
          const publicSolves = await fetchFriendSubmissions(friend.leetcode_username).catch(() => []);
          const ledger = friend.codeforces_username ? await api.recentSolves(friend.id, 10) : [];
          const combined: FriendSolve[] = [
            ...publicSolves.map(s => ({ ...s, friend, platform: "leetcode", problemUrl: `https://leetcode.com/problems/${s.titleSlug}/` })),
            ...ledger.map(s => ({ title: s.title, titleSlug: s.title_slug, timestamp: String(new Date(s.solved_at).getTime() / 1000), friend, platform: s.platform || "leetcode", problemUrl: s.problem_url || s.leetcode_url })),
          ];
          const unique = [...new Map(combined.map(s => [`${s.platform}-${s.titleSlug}`, s])).values()];
          results.push(...unique);
          if (active) setItems([...results].sort((a, b) => Number(b.timestamp) - Number(a.timestamp)));
        } catch { failures++; if (active) setFailed(failures); }
      }
    }
    Promise.all(Array.from({ length: Math.min(4, friends.length) }, worker)).then(() => {
      if (!active) return;
      setItems(results.sort((a, b) => Number(b.timestamp) - Number(a.timestamp)));
      setFailed(failures); setBusy(false);
    });
    return () => { active = false; };
  }, [signature, refresh]);
  const visible = items.filter(s => filter === "all" || String(s.friend.id) === filter).slice(0, 15);
  return <section className="friends-practice" aria-labelledby="friends-practice-title">
    <div className="section-header study-plan-top"><h3 className="section-title" id="friends-practice-title">What are my friends up to?</h3><button className="chip-btn" disabled={busy || !friends.length} onClick={() => setRefresh(n => n + 1)}>{busy ? "Checking…" : "Refresh"}</button></div>
    <p className="progress-note">Latest public accepted questions from people in your groups.</p>
    {friends.length > 1 && <select aria-label="Filter activity by friend" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All friends</option>{friends.map(f => <option value={f.id} key={f.id}>{f.name}</option>)}</select>}
    {busy && <p className="progress-note" role="status">Catching up with your friends…</p>}
    {!friends.length && <p className="progress-note">Join or create a group in Leaderboards to see your friends here.</p>}
    {failed > 0 && <p className="progress-error" role="status">Couldn't check {failed} public profile{failed === 1 ? "" : "s"}. Refresh to try again.</p>}
    {!busy && friends.length > 0 && !visible.length && !failed && <p className="progress-note">No recent public solves yet. Your friends' next accepted question will appear here.</p>}
    <ul>{visible.map(s => <li key={`${s.friend.id}-${s.platform}-${s.titleSlug}`}><div className="friend-practice-avatar" aria-hidden="true">{s.friend.name.slice(0, 1).toUpperCase()}</div><div><strong>{s.friend.name}</strong><a href={s.problemUrl || `https://leetcode.com/problems/${s.titleSlug}/`} target="_blank" rel="noreferrer">{s.title} ↗</a><small className="solve-platform">{s.platform === "codeforces" ? "Codeforces" : "LeetCode"}</small><time dateTime={new Date(Number(s.timestamp) * 1000).toISOString()}>{new Date(Number(s.timestamp) * 1000).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</time></div></li>)}</ul>
  </section>;
}
