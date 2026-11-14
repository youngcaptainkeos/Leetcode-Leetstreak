import { formatPoints } from "./points";

type StoredBase = {
  difficulty?: string;
  raw_base_points?: number;
  contest_rating?: number | null;
  ac_rate?: number | null;
  base_points?: number;
  base_award?: number;
  streak_multiplier?: number;
};

export type PointDetailRow = { label: string; value: string };

const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
const points = (value: number) => `${formatPoints(value)} pts`;
const adjustment = (value: number) => `${value < 0 ? "−" : "+"}${points(Math.abs(value))}`;

/** Explain saved award inputs; never reprice a question using current metadata. */
export function basePointDetails(base: StoredBase, platform = "leetcode"): PointDetailRow[] {
  const raw = base.raw_base_points;
  const adjusted = base.base_points;
  // Old protected awards may not contain formula inputs. Do not invent a
  // historical acceptance rate or mistake API defaults for a recorded formula.
  if (!finite(raw) || raw <= 0 || !finite(adjusted) || adjusted <= 0) {
    return [{ label: "Recorded base credit", value: points(base.base_award ?? 0) }];
  }

  const rows: PointDetailRow[] = [];
  const difficultyBase = platform === "leetcode"
    ? ({ Easy: 8, Medium: 15, Hard: 24 } as Record<string, number>)[base.difficulty ?? ""]
    : undefined;
  const rated = finite(base.contest_rating) && base.contest_rating > 0;
  if (difficultyBase !== undefined) {
    rows.push({ label: `Base points (${base.difficulty})`, value: points(difficultyBase) });
    if (rated) {
      rows.push({ label: `Contest rating (${formatPoints(base.contest_rating)})`, value: adjustment(raw - difficultyBase) });
    }
  } else {
    rows.push({ label: platform === "codeforces" ? "Rating base points" : "Base points", value: points(raw) });
  }

  if (platform === "leetcode" && !rated && finite(base.ac_rate)) {
    const rate = base.ac_rate.toLocaleString(undefined, { maximumFractionDigits: 1 });
    const delta = adjusted - raw;
    rows.push({ label: `Acceptance-rate ${delta < 0 ? "deduction" : "adjustment"} (${rate}%)`, value: adjustment(delta) });
  }
  rows.push({ label: "Adjusted base points", value: points(adjusted) });
  rows.push({ label: "Streak multiplier", value: finite(base.streak_multiplier)
    ? `${base.streak_multiplier.toLocaleString(undefined, { maximumFractionDigits: 3 })}×` : "—" });
  rows.push({ label: "Base credit after multiplier", value: points(base.base_award ?? 0) });
  return rows;
}
