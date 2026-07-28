import { MarketTiming } from "../lib/api";
import styles from "./MarketTimingCard.module.css";

export const MarketTimingCard = ({ state }: { state: MarketTiming }) => (
  <section className={styles.card}>
    <h2>Market timing</h2>
    <span className={`${styles.badge} ${styles[state]}`}>{state}</span>
  </section>
);
