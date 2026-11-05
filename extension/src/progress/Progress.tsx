import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { GroupResponse, GroupMember } from "../lib/api";
import { getStored, setStored } from "../storage";
import { STUDY_PLANS, PRACTICE_REFRESH, PracticeSnapshot, ProgressState, Submission, dailySolved, fetchPractice, fetchFriendSubmissions, planCounts, progressKey, readProgress } from "./data";
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
  const [state, setState] = useState<ProgressState | null>(null);
  const [selected, setSelected] = useState(STUDY_PLANS[0].slug);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [notice, setNotice] = useState("");
  const [showQuestions, setShowQuestions] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  useEffect(() => {
    let active = true;
    getStored(key).then(raw => { if (active) { const saved = readProgress(raw); setState(saved); setSelected(saved.followed[0] || STUDY_PLANS[0].slug); } });
    return () => { active = false; };
  }, [key]);
  useEffect(() => { if (state) void setStored(key, JSON.stringify(state)); }, [key, state]);
  const loaded = state !== null;
  useEffect(() => {
    if (!loaded || !snapshot) return;
    setState(prev => prev ? { ...prev, observed: [...new Set([...prev.observed, ...snapshot.submissions.map(s => s.titleSlug)])] } : prev);
  }, [loaded, snapshot]);

  if (!state) return <div className="centered muted">Loading your progress…</div>;
  const plan = STUDY_PLANS.find(p => p.slug === selected) || STUDY_PLANS[0];
  const solved = new Set([...state.manual, ...state.observed]);
  const automatic = new Set(state.observed);
  const count = planCounts(plan, state);
  const following = state.followed.includes(plan.slug);
  function toggleFollow() {
    setState(prev => prev ? { ...prev, followed: following ? prev.followed.filter(s => s !== plan.slug) : [...prev.followed, plan.slug] } : prev);
    setNotice(following ? `${plan.name} removed from following. Your progress is saved.` : `Following ${plan.name}. One question at a time!`);
  }
  function toggleSolved(slug: string) {
    if (!state) return;
    const manual = state.manual.includes(slug) ? state.manual.filter(s => s !== slug) : [...state.manual, slug];
    const next = { ...state, manual };
    const result = planCounts(plan, next);
    setState(next);
    setNotice(result.done === result.total ? `✦ ${plan.name} complete! Every question, done.` : `${result.done} of ${result.total} completed. Progress saved.`);
  }
  const visibleGroups = plan.planSubGroups.map(g => ({ ...g, questions: g.questions.filter(q =>
    q.title.toLowerCase().includes(search.toLowerCase()) && (filter === "all" || (filter === "done" ? solved.has(q.titleSlug) : !solved.has(q.titleSlug)))) })).filter(g => g.questions.length);
  return <div className="progress-panel" id="progress-panel" role="tabpanel" aria-labelledby="progress-menu">
    {active && <FriendsActivity key={`${userId}-${username}`} userId={userId} groups={groups} />}
    <div className="section-header study-plans-heading"><h2 className="section-title">Study plans</h2></div>
    <div className="study-plan-list" id="study-plans" aria-label="Study plans">{STUDY_PLANS.map(p => { const c = planCounts(p, state); return <button key={p.slug} className={`study-plan-option ${p.slug === plan.slug ? "selected" : ""}`} aria-pressed={p.slug === plan.slug} onClick={() => { setSelected(p.slug); setSearch(""); setFilter("all"); setNotice(""); setShowQuestions(false); setExpandedGroups([]); }}>
      <span><strong>{p.name}</strong><small>{state.followed.includes(p.slug) ? "Following · " : ""}{c.done}/{c.total} solved</small></span><span className="plan-mini-meter" aria-hidden="true"><i style={{ width: `${c.percent}%` }} /></span><b>{c.percent}%</b>
    </button>; })}</div>
    <section className="study-plan-detail" aria-label={`${plan.name} progress`}>
      <div className="study-plan-top"><div><h3>{plan.name}</h3><a href={`https://leetcode.com/studyplan/${plan.slug}/`} target="_blank" rel="noreferrer">View on LeetCode ↗</a></div><button className={`chip-btn ${following ? "is-following" : ""}`} aria-pressed={following} onClick={toggleFollow}>{following ? "✓ Following" : "+ Follow plan"}</button></div>
      <div className="plan-progress-label"><strong>{count.done}<span> / {count.total} completed</span></strong><b>{count.percent}%</b></div>
      <div className="plan-progress-track" role="progressbar" aria-label={`${plan.name} completion`} aria-valuenow={count.done} aria-valuemin={0} aria-valuemax={count.total}><div style={{ width: `${count.percent}%` }} /></div>
      {count.next ? <a className="plan-continue" href={`https://leetcode.com/problems/${count.next.titleSlug}/`} target="_blank" rel="noreferrer"><span>UP NEXT<strong>{count.next.title}</strong></span><span aria-hidden="true">↗</span></a> : <p className="plan-complete">✦ Plan complete. Enjoy that milestone!</p>}
      <p className="progress-note">Recent public accepted solves are checked automatically. Mark older solves yourself. Checkmarks and followed plans are saved in this browser for this account.</p>
      {error && <p className="progress-error" role="status">Automatic checking is unavailable. Your saved progress is still here.</p>}
      <div className="progress-notice" role="status" aria-live="polite">{notice}</div>
      <div className="plan-question-controls"><button className="chip-btn" aria-expanded={showQuestions} aria-controls="plan-question-list" onClick={() => setShowQuestions(value => !value)}>{showQuestions ? "Hide questions ↑" : "Show questions ↓"}</button>{showQuestions && <button className="chip-btn" onClick={() => { const allOpen = visibleGroups.every(g => expandedGroups.includes(g.name)); setExpandedGroups(allOpen ? [] : visibleGroups.map(g => g.name)); }}>{visibleGroups.length > 0 && visibleGroups.every(g => expandedGroups.includes(g.name)) ? "Collapse all" : "Expand all"}</button>}</div>
      {showQuestions && <div id="plan-question-list"><div className="plan-tools"><input type="search" aria-label="Search plan questions" placeholder="Find a question…" value={search} onChange={e => { setSearch(e.target.value); if (e.target.value) setExpandedGroups(plan.planSubGroups.map(g => g.name)); }} /><select aria-label="Filter plan questions" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All questions</option><option value="todo">To do</option><option value="done">Completed</option></select></div>
      <div className="plan-question-groups">{visibleGroups.length ? visibleGroups.map(group => <details key={`${plan.slug}-${group.name}`} open={expandedGroups.includes(group.name)} onToggle={e => { const open = e.currentTarget.open; setExpandedGroups(previous => open ? previous.includes(group.name) ? previous : [...previous, group.name] : previous.includes(group.name) ? previous.filter(name => name !== group.name) : previous); }}>
        <summary>{group.name}<span>{group.questions.filter(q => solved.has(q.titleSlug)).length}/{group.questions.length}</span></summary>
        <ul>{group.questions.map(q => <li key={q.titleSlug} className={solved.has(q.titleSlug) ? "question-done" : ""}>
          <input type="checkbox" checked={solved.has(q.titleSlug)} disabled={automatic.has(q.titleSlug)} aria-label={`${q.title}${automatic.has(q.titleSlug) ? ": automatically detected as solved" : ": mark complete"}`} onChange={() => toggleSolved(q.titleSlug)} />
          <a href={`https://leetcode.com/problems/${q.titleSlug}/`} target="_blank" rel="noreferrer">{q.title}<small className={`question-difficulty ${q.difficulty.toLowerCase()}`}>{q.difficulty.toLowerCase()}{automatic.has(q.titleSlug) ? " · auto" : ""}</small></a><span aria-hidden="true">↗</span>
        </li>)}</ul>
      </details>) : <p className="progress-note">No questions match this filter.</p>}</div></div>}
    </section>
  </div>;
}

interface FriendSolve extends Submission { friend: GroupMember }
function FriendsActivity({ userId, groups }: { userId: number; groups: GroupResponse[] }) {
  const friends = [...new Map(groups.flatMap(g => g.members).filter(m => m.id !== userId).map(m => [m.id, m])).values()];
  const signature = JSON.stringify(friends.map(f => [f.id, f.leetcode_username]).sort());
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
          const solves = await fetchFriendSubmissions(friend.leetcode_username);
          const unique = [...new Map(solves.map(s => [s.titleSlug, s])).values()];
          results.push(...unique.map(s => ({ ...s, friend })));
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
    <ul>{visible.map(s => <li key={`${s.friend.id}-${s.titleSlug}`}><div className="friend-practice-avatar" aria-hidden="true">{s.friend.name.slice(0, 1).toUpperCase()}</div><div><strong>{s.friend.name}</strong><a href={`https://leetcode.com/problems/${s.titleSlug}/`} target="_blank" rel="noreferrer">{s.title} ↗</a><time dateTime={new Date(Number(s.timestamp) * 1000).toISOString()}>{new Date(Number(s.timestamp) * 1000).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</time></div></li>)}</ul>
  </section>;
}
