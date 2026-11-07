/** Round only for display; stored scores and ranking inputs keep their precision. */
export function formatPoints(value: number | null | undefined, fallback = "—"): string {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.round(value).toLocaleString(undefined, { maximumFractionDigits: 0 })
    : fallback;
}
