import { HurstVeto } from "../lib/api";
import { HurstBadge } from "../signals/HurstBadge";
import styles from "./TickerCard.module.css";

export const TickerCard = ({
  ticker,
  name,
  hurstState,
}: {
  ticker: string;
  name: string;
  hurstState?: HurstVeto;
}) => {
  const imageSrc = `https://icons.penylo.dev/${ticker}`;

  return (
    <div className={styles.tickerCard}>
      <div className={styles.tickerCardImage}>
        <img src={imageSrc} alt="" />
      </div>
      <div className="tickerCardText">
        <div className={styles.tickerCardSymbol}>{ticker}</div>
        <div className={styles.tickerCardName}>{name}</div>
        <HurstBadge state={hurstState} />
      </div>
    </div>
  );
};
