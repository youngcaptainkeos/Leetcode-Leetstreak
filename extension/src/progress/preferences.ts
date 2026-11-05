export type StartupTab = "last" | "progress" | "leaderboards";
export function readStartupTab(value: string | null): StartupTab {
  return value === "progress" || value === "leaderboards" ? value : "last";
}
export function startupTabKey(userId: number): string { return `codestreak_startup_tab_${userId}`; }
export function resolveStartupTab(preference: StartupTab, lastUsed: string | null): "progress" | "leaderboards" {
  return preference === "last" ? lastUsed === "progress" ? "progress" : "leaderboards" : preference;
}
