import { CanslimResult } from "../lib/api";
import { CriterionPill } from "./CriterionPill";
import { CANSLIM_LETTERS, letterStatuses } from "./status";
import styles from "./CanslimScreenerTable.module.css";

export const CanslimScreenerTable = ({
  results,
  onSelectTicker,
}: {
  results: CanslimResult[];
  onSelectTicker?: (ticker: string) => void;
}) => {
  const qualifying = results.filter((result) => result.available_criteria_met).length;

  return (
    <section className={styles.card}>
      <header className={styles.header}>
        <h2>CANSLIM Screener</h2>
        <span className={styles.subtitle}>
          {qualifying} of {results.length} meet all available criteria (N · S · L · M) — C, A, I are
          not available with current data sources, so this is not a full CANSLIM qualification.
        </span>
      </header>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.tickerCol}>Ticker</th>
              <th className={styles.rsCol}>RS</th>
              {CANSLIM_LETTERS.map((letter) => (
                <th key={letter}>{letter}</th>
              ))}
              <th className={styles.countCol}>N·S·L·M</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => {
              const statuses = letterStatuses(result);
              const lCriterion = result.criteria.L;
              const rs =
                lCriterion && "rs_rating" in lCriterion ? (lCriterion.rs_rating as number) : null;
              return (
                <tr
                  key={result.ticker}
                  className={result.available_criteria_met ? styles.qualifies : undefined}
                  onClick={() => onSelectTicker?.(result.ticker)}
                >
                  <td className={styles.tickerCol}>{result.ticker}</td>
                  <td className={styles.rsCol}>{rs !== null ? Math.round(rs) : "—"}</td>
                  {CANSLIM_LETTERS.map((letter) => (
                    <td key={letter}>
                      <CriterionPill label={letter} status={statuses[letter]} showLabel={false} />
                    </td>
                  ))}
                  <td className={styles.countCol}>{result.available_criteria_count}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};
