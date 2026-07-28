import { OptionOverlay } from "../lib/api";
import styles from "./OptionOverlayCard.module.css";

export const OptionOverlayCard = ({
  state,
}: {
  state: OptionOverlay;
}) => (
  <section className={styles.card}>
    <h2>Option overlay</h2>
    <span className={styles.state}>{state.replace("_", " ")}</span>
  </section>
);
