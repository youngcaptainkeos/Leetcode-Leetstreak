import React from "react";
import type { DashboardResponse, DayCount } from "./lib/api";

export type MetricsPlatform = "all" | "leetcode" | "codeforces";
export interface PlatformMetrics {
  current_streak: number; today_count: number; weekly_total: number; monthly_total: number;
  total_solved: number; points?: number; easy_count: number; medium_count: number;
  hard_count: number; codeforces_count: number; rated_count: number; unrated_count: number;
  last_7_days: DayCount[];
}
export function metricsFor(data: DashboardResponse, platform: MetricsPlatform): PlatformMetrics | null {
  if (data.platform_stats?.[platform]) return data.platform_stats[platform];
  if (platform !== "all") return null;
  return { ...data, total_solved: data.easy_count + data.medium_count + data.hard_count + (data.codeforces_count || 0), codeforces_count: data.codeforces_count || 0, rated_count: 0, unrated_count: 0 };
}
export function PlatformSelector({ platform, onChange }: { platform: MetricsPlatform; onChange: (next: MetricsPlatform) => void }) {
  return <div className="metrics-source" role="group" aria-label="Stats source">{([['all', 'All'], ['leetcode', 'LeetCode'], ['codeforces', 'Codeforces']] as const).map(([value, label]) => <button type="button" key={value} aria-pressed={platform === value} onClick={() => onChange(value)}>{label}</button>)}</div>;
}
export function MetricsPanel({ data, platform, onChange, showFilter = true, loading = false }: { data: DashboardResponse | null; platform: MetricsPlatform; onChange: (next: MetricsPlatform) => void; showFilter?: boolean; loading?: boolean }) {
  const metrics = data ? metricsFor(data, platform) : null;
  const pills: [string, number, string][] = metrics ? platform === "codeforces" ? [['Rated', metrics.rated_count, 'medium'], ['Unrated', metrics.unrated_count, 'hard'], ['Total', metrics.total_solved, 'total']] : [
    ['Easy', metrics.easy_count, 'easy'], ['Med', metrics.medium_count, 'medium'], ['Hard', metrics.hard_count, 'hard'],
    ...(platform === 'all' ? [['CF', metrics.codeforces_count, 'total'] as [string, number, string]] : []), ['Total', metrics.total_solved, 'total'],
  ] : [];
  return <div className="platform-metrics">
    {showFilter && <PlatformSelector platform={platform} onChange={onChange} />}
    {data && platform === "codeforces" && !data.codeforces_username && <p className="tiny muted">No Codeforces account connected.</p>}
    {!data ? <p className="tiny muted" role="status">{loading ? "Loading profile metrics…" : "Profile metrics are unavailable."}</p> : !metrics ? <p className="tiny muted" role="status">Platform breakdown is unavailable. Choose All to view combined stats.</p> : <>
      <div className="streak-hero"><img src="/main_fire.png" alt="" className="hero-flame-img" /><span className="streak-count">{metrics.current_streak}</span></div>
      <div className="streak-label">{platform === "all" ? "COMBINED" : platform === "codeforces" ? "CODEFORCES" : "LEETCODE"} DAY STREAK</div>
      <p className="metrics-points">{metrics.points === undefined ? "Points unavailable" : `${metrics.points.toLocaleString(undefined, { maximumFractionDigits: 2 })} points`}</p>
      <div className="stat-row">{[['Today', metrics.today_count], ['This Week', metrics.weekly_total], ['This Month', metrics.monthly_total]].map(([label, value]) => <div className="stat" key={label}><div className="stat-value">{value}</div><div className="tiny muted">{label}</div></div>)}</div>
      <div className="diff-pills metrics-pills" style={{ gridTemplateColumns: `repeat(${pills.length}, minmax(0, 1fr))` }}>{pills.map(([label, value, style]) => <span className={`diff-pill ${style}`} title={`${label}: ${value}`} key={label}>{label} {value}</span>)}</div>
    </>}
  </div>;
}
