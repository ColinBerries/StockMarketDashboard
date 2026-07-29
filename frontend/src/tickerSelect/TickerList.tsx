import "./TickerSelect.css";
import { TickerCard } from "./TickerCard";
import { HurstVeto } from "../lib/api";

export interface TickerOption {
  ticker: string;
  name: string;
  icon?: string;
}

export const SelectTickerList = ({
  tickerList,
  setTicker,
  hurstVeto,
  query,
  onLoadQuery,
}: {
  tickerList: TickerOption[];
  hurstVeto: Record<string, HurstVeto>;
  setTicker: (option: TickerOption) => void;
  query: string;
  onLoadQuery?: () => void;
}) => {
  return (
    <div className="tickerList">
      {onLoadQuery && (
        <button key="load-query" onClick={onLoadQuery} className="tickerListLoadQuery">
          Load "{query}" →
        </button>
      )}
      {tickerList.map((item) => (
        <button key={item.ticker} onClick={() => setTicker(item)}>
          <TickerCard name={item.name} ticker={item.ticker} icon={item.icon} hurstState={hurstVeto[item.ticker]} />
        </button>
      ))}
      {tickerList.length === 0 && !onLoadQuery && (
        <p className="tickerListEmpty">No matches in the quick list — type a full symbol and press Enter.</p>
      )}
    </div>
  );
};
