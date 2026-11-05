export interface PlanView { showQuestions: boolean; expandedGroups: string[] }
export interface ProgressView { selected: string; plans: Record<string, PlanView> }
export const emptyPlanView = (): PlanView => ({ showQuestions: false, expandedGroups: [] });
export function readProgressView(raw: string | null): ProgressView {
  const empty = { selected: "", plans: {} };
  try {
    const data = JSON.parse(raw || "null");
    if (!data || typeof data !== "object" || Array.isArray(data)) return empty;
    const entries = data.plans && typeof data.plans === "object" && !Array.isArray(data.plans) ? Object.entries(data.plans).slice(0, 1000) : [];
    return {
      selected: typeof data.selected === "string" && /^[a-z0-9-]{1,100}$/.test(data.selected) ? data.selected : "",
      plans: Object.fromEntries(entries.filter(([slug, value]) => /^[a-z0-9-]{1,100}$/.test(slug) && value && typeof value === "object").map(([slug, value]) => {
        const item = value as Partial<PlanView>;
        return [slug, { showQuestions: item.showQuestions === true, expandedGroups: Array.isArray(item.expandedGroups) ? [...new Set(item.expandedGroups.filter((name): name is string => typeof name === "string" && name.length <= 150))].slice(0, 200) : [] }];
      })),
    };
  } catch { return empty; }
}
