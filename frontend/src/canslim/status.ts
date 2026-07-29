import { CanslimCriterion, CanslimResult } from "../lib/api";
import { CriterionStatus } from "./CriterionPill";

function singleStatus(criterion: CanslimCriterion | null | undefined): CriterionStatus {
  if (!criterion) return "unknown";
  if ("status" in criterion && criterion.status === "unavailable") return "unavailable";
  if (criterion.pass === true) return "pass";
  if (criterion.pass === false) return "fail";
  return "unknown";
}

/** A letter with two sub-checks (N, S) only "passes" if both do. */
function combinedStatus(...parts: Array<CanslimCriterion | null | undefined>): CriterionStatus {
  const statuses = parts.map(singleStatus);
  if (statuses.includes("unavailable")) return "unavailable";
  if (statuses.includes("unknown")) return "unknown";
  return statuses.every((s) => s === "pass") ? "pass" : "fail";
}

export interface LetterStatuses {
  C: CriterionStatus;
  A: CriterionStatus;
  N: CriterionStatus;
  S: CriterionStatus;
  L: CriterionStatus;
  I: CriterionStatus;
  M: CriterionStatus;
}

export const CANSLIM_LETTERS: Array<keyof LetterStatuses> = ["C", "A", "N", "S", "L", "I", "M"];

export function letterStatuses(result: CanslimResult): LetterStatuses {
  return {
    C: singleStatus(result.criteria.C),
    A: singleStatus(result.criteria.A),
    N: combinedStatus(result.criteria.N_high, result.criteria.N_breakout),
    S: combinedStatus(result.criteria.S_shares, result.criteria.S_volume),
    L: singleStatus(result.criteria.L),
    I: singleStatus(result.criteria.I),
    M: singleStatus(result.criteria.M),
  };
}
