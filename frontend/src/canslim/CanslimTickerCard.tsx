import { CanslimResult } from "../lib/api";
import { CriterionPill } from "./CriterionPill";
import { CANSLIM_LETTERS, letterStatuses } from "./status";
import styles from "./CanslimTickerCard.module.css";

export const CanslimTickerCard = ({
  result,
  error,
}: {
  result: CanslimResult | null;
  error?: string;
}) => (
  <section className={styles.card}>
    <h2>CANSLIM {result ? `— ${result.available_criteria_count} of N·S·L·M` : ""}</h2>
    {error && <p className={styles.error}>Unavailable — {error}</p>}
    {result && (
      <div className={styles.pills}>
        {CANSLIM_LETTERS.map((letter) => (
          <CriterionPill key={letter} label={letter} status={letterStatuses(result)[letter]} />
        ))}
      </div>
    )}
  </section>
);
