import { useState } from "react";
import { HurstVeto } from "../lib/api";
import { HurstBadge } from "../signals/HurstBadge";
import styles from "./TickerCard.module.css";

export const TickerCard = ({
  ticker,
  name,
  hurstState,
  icon,
}: {
  ticker: string;
  name: string;
  hurstState?: HurstVeto;
  icon?: string;
}) => {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <div className={styles.tickerCard}>
      <div className={styles.tickerCardImage}>
        {!icon || imageFailed ? (
          <div className={styles.tickerCardFallback}>{ticker.slice(0, 2)}</div>
        ) : (
          <img src={icon} alt="" onError={() => setImageFailed(true)} />
        )}
      </div>
      <div className="tickerCardText">
        <div className={styles.tickerCardSymbol}>{ticker}</div>
        <div className={styles.tickerCardName}>{name}</div>
        <HurstBadge state={hurstState} />
      </div>
    </div>
  );
};
