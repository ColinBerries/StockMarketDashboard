import { TickerZodObject } from "./tickersZodObject";
import "./TickerSelect.css";
import { TickerCard } from "./TickerCard";
import { HurstVeto } from "../lib/api";

export const SelectTickerList = ({
  tickerList,
  setTicker,
  hurstVeto,
}: {
  tickerList: TickerZodObject;
  hurstVeto: Record<string, HurstVeto>;
  setTicker: React.Dispatch<
    React.SetStateAction<{
      name: string;
      ticker: string;
    }>
  >;
}) => {
  const tickerHtmlList = tickerList.map((item) => {
    return (
      <button
        key={item.Item.ticker}
        onClick={() => {
          setTicker({
            name: item.Item.title,
            ticker: item.Item.ticker,
          });
        }}
      >
        <TickerCard
          name={item.Item.title}
          ticker={item.Item.ticker}
          hurstState={hurstVeto[item.Item.ticker]}
        />
      </button>
    );
  });

  return <div className="tickerList">{tickerHtmlList}</div>;
};
