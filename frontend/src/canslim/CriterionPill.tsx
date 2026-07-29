import styles from "./CriterionPill.module.css";

export type CriterionStatus = "pass" | "fail" | "unavailable" | "unknown";

const SYMBOLS: Record<CriterionStatus, string> = {
  pass: "✓",
  fail: "✗",
  unavailable: "–",
  unknown: "?",
};

const TOOLTIPS: Record<CriterionStatus, string> = {
  pass: "meets this criterion",
  fail: "does not meet this criterion",
  unavailable: "not available with current data sources",
  unknown: "not enough data to evaluate",
};

export const CriterionPill = ({
  label,
  status,
  showLabel = true,
}: {
  label: string;
  status: CriterionStatus;
  showLabel?: boolean;
}) => (
  <span className={`${styles.pill} ${styles[status]}`} title={`${label}: ${TOOLTIPS[status]}`}>
    {showLabel ? label : SYMBOLS[status]}
  </span>
);
