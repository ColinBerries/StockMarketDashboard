import styles from "./StatBadge.module.css";

export type BadgeTone = "positive" | "negative" | "neutral";

interface StatBadgeProps {
  label: string;
  value: string;
  detail?: string;
  tone: BadgeTone;
  error?: string;
}

export const StatBadge = ({ label, value, detail, tone, error }: StatBadgeProps) => (
  <div className={styles.badge}>
    <span className={`${styles.dot} ${styles[tone]}`} />
    <div>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{error ? "—" : value}</div>
      {!error && detail && <div className={styles.detail}>{detail}</div>}
      {error && <div className={styles.detail}>{error}</div>}
    </div>
  </div>
);
