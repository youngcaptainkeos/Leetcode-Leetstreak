import { formatPoints } from "./points";

type StoredPoints = {
  difficulty?: string;
  raw_base_points?: number;
  contest_rating?: number | null;
  ac_rate?: number | null;
  ac_multiplier?: number;
  base_points?: number;
  base_award?: number;
  daily_award?: number;
  revision_award?: number;
  streak_multiplier?: number;
};

export type PointDetailRow = { label: string; value: string };

const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);
const points = (value: number) => `${formatPoints(value)} pts`;
const decimal = (value: number, digits = 3) => value.toLocaleString(undefined, { maximumFractionDigits: digits });

/** Display only the saved scoring path and rewards that actually earned credit. */
export function pointDetails(stored: StoredPoints, platform = "leetcode"): PointDetailRow[] {
  const raw = stored.raw_base_points;
  const adjusted = stored.base_points;
  const hasFormula = finite(raw) && raw > 0 && finite(adjusted) && adjusted > 0;
  const rated = finite(stored.contest_rating) && stored.contest_rating > 0;
  const rows: PointDetailRow[] = [];

  if (hasFormula) {
    if (platform === "codeforces") {
      rows.push({ label: rated ? `Base points (CF ${formatPoints(stored.contest_rating)})` : "Base points", value: points(raw) });
    } else if (rated) {
      rows.push({ label: `Base points (ZeroTrac ${formatPoints(stored.contest_rating)})`, value: points(raw) });
    } else {
      rows.push({ label: stored.difficulty ? `Base points (${stored.difficulty})` : "Base points", value: points(raw) });
      if (finite(stored.ac_rate)) {
        const factor = finite(stored.ac_multiplier) ? stored.ac_multiplier : adjusted / raw;
        rows.push({ label: `Adjusted base (AR ${decimal(stored.ac_rate, 1)}%)`,
          value: `${formatPoints(raw)} × ${decimal(factor, 4)} = ${points(adjusted)}` });
      }
    }
  } else if ((stored.base_award ?? 0) > 0) {
    // Protected historical awards can lack formula inputs. Do not fabricate a
    // raw base, acceptance rate, or multiplier from a combined credited total.
    rows.push({ label: "Recorded base credit", value: points(stored.base_award!) });
  }

  if (platform !== "codeforces" && (stored.daily_award ?? 0) > 0) {
    rows.push({ label: "Daily question bonus", value: points(stored.daily_award!) });
  }
  if ((stored.revision_award ?? 0) > 0) {
    rows.push({ label: "Revision points", value: points(stored.revision_award!) });
  }
  if (hasFormula && finite(stored.streak_multiplier)) {
    rows.push({ label: "Streak multiplier", value: `${decimal(stored.streak_multiplier)}×` });
  }
  return rows;
}
