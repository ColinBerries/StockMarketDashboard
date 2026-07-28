import { PortfolioLegs } from "../lib/api";
import styles from "./LongShortTable.module.css";

export const LongShortTable = ({
  book,
}: {
  book: PortfolioLegs["long_short_book"];
}) => (
  <section className={styles.card}>
    <h2>Long / short book</h2>
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Long</th>
          <th>Short</th>
        </tr>
      </thead>
      <tbody>
        {Array.from({
          length: Math.max(book.long.length, book.short.length),
        }).map((_, index) => (
          <tr key={`${book.long[index] ?? ""}-${book.short[index] ?? ""}`}>
            <td>{book.long[index] ?? "—"}</td>
            <td>{book.short[index] ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
);
