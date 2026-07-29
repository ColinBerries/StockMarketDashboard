import { useMemo, useState } from "react";
import "./TickerSelect.css";
import { HurstVeto } from "../lib/api";
import { tickers } from "../tickers";
import { SelectTickerList, TickerOption } from "./TickerList";

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
  const [query, setQuery] = useState("");

  const matches: TickerOption[] = useMemo(() => {
    const trimmed = query.trim().toUpperCase();
    const entries = Object.entries(tickers);
    const filtered = trimmed
      ? entries.filter(
          ([ticker, info]) =>
            ticker.startsWith(trimmed) || info.companyName.toUpperCase().includes(trimmed),
        )
      : entries;
    return filtered.map(([ticker, info]) => ({
      ticker,
      name: info.companyName,
      icon: info.icon,
    }));
  }, [query]);

  const loadTicker = (ticker: string, name?: string) => {
    const upper = ticker.trim().toUpperCase();
    if (!upper) return;
    setActiveTicker({ ticker: upper, name: name ?? tickers[upper]?.companyName ?? upper });
    setQuery("");
  };

  const trimmedQuery = query.trim().toUpperCase();
  const hasExactMatch = matches.some((match) => match.ticker === trimmedQuery);

  return (
    <div className="tickerSelect">
      <div className="tickerSelectHeader">
        <div className="tickerSelectHeaderInner">
          <span className="smallText">Search Tickers:</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && trimmedQuery) {
                loadTicker(trimmedQuery);
              }
            }}
            placeholder="Type any symbol, e.g. TSLA"
          />
        </div>
      </div>
      <SelectTickerList
        tickerList={matches}
        setTicker={(option) => loadTicker(option.ticker, option.name)}
        hurstVeto={hurstVeto}
        query={trimmedQuery}
        onLoadQuery={!trimmedQuery || hasExactMatch ? undefined : () => loadTicker(trimmedQuery)}
      />
    </div>
  );
};
