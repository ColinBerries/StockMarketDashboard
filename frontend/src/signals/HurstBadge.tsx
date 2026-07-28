import { HurstVeto } from "../lib/api";
import styles from "./HurstBadge.module.css";

export const HurstBadge = ({ state }: { state?: HurstVeto }) => {
  if (!state) {
    return null;
  }

  return (
    <span className={`${styles.badge} ${styles[state]}`}>
      {state.replace("_", " ")}
    </span>
  );
};
