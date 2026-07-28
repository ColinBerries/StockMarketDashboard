import { useState } from "react";
import { TickerZodObject, tickerZodObject } from "./tickersZodObject";
import { SelectTickerList } from "./TickerList";
import "./TickerSelect.css";
import { HurstVeto } from "../lib/api";

export const TickerSelect = ({
  setActiveTicker,
  hurstVeto,
}: {
  hurstVeto: Record<string, HurstVeto>;
  setActiveTicker: React.Dispatch<
    React.SetStateAction<{
      name: string;
      ticker: string;
    }>
  >;
}) => {
  const [tickerList, setTickerList] = useState<TickerZodObject>([]);

  const searchTickerList = async (event: React.FormEvent<HTMLInputElement>) => {
    const currentSearchTerm = event.currentTarget.value;
    const values = await fetch(
      `https://tickers.penylo.dev/v2/search?q=${currentSearchTerm}`,
    );
    console.info(values);
    const zodParse = tickerZodObject.safeParse(await values.json());
    if (!zodParse.error) {
      setTickerList(zodParse.data);
    }
  };

  return (
    <div className="tickerSelect">
      <div className="tickerSelectHeader">
        <div className="tickerSelectHeaderInner">
          <span className="smallText">Search Tickers:</span>
          <input onInput={searchTickerList}></input>
        </div>
      </div>
      <SelectTickerList
        tickerList={tickerList}
        setTicker={setActiveTicker}
        hurstVeto={hurstVeto}
      />
    </div>
  );
};
