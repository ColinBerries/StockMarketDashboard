import { PortfolioLegs } from "../lib/api";
import styles from "./UniverseList.module.css";

export const UniverseList = ({
  universe,
  book,
  universeErrors,
}: {
  universe: string[];
  book: PortfolioLegs["long_short_book"];
  universeErrors?: Record<string, string>;
}) => {
  const longSet = new Set(book.long);
  const shortSet = new Set(book.short);

  return (
    <section className={styles.card}>
      <h2>Universe ({universe.length})</h2>
      <div className={styles.chips}>
        {universe.map((ticker) => {
          const failed = universeErrors?.[ticker];
          const tone = failed
            ? styles.failed
            : longSet.has(ticker)
              ? styles.long
              : shortSet.has(ticker)
                ? styles.short
                : styles.neutral;
          return (
            <span
              key={ticker}
              className={`${styles.chip} ${tone}`}
              title={failed ? `Skipped: ${failed}` : undefined}
            >
              {ticker}
            </span>
          );
        })}
      </div>
      {universeErrors && Object.keys(universeErrors).length > 0 && (
        <p className={styles.note}>
          {Object.keys(universeErrors).length} ticker(s) skipped this refresh
          (rate-limited or unavailable) — hover a grayed-out symbol for detail.
        </p>
      )}
    </section>
  );
};
