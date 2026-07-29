import { formatCurrency, formatPercent } from "./lib/format";

interface TopBarProps {
  activeTicker: { name: string; ticker: string };
  price: number | null;
  change: number | null;
  changePct: number | null;
}

export const TopBar = ({ activeTicker, price, change, changePct }: TopBarProps) => {
  const tone = change === null ? "flat" : change > 0 ? "up" : change < 0 ? "down" : "flat";

  return (
    <div className="topBar">
      <div className="topBarIdentity">
        <span className="topBarSymbol">{activeTicker.ticker}</span>
        <span className="topBarName">{activeTicker.name}</span>
      </div>
      <div className="topBarPrice">
        <span className="topBarPriceValue">{formatCurrency(price)}</span>
        {change !== null && (
          <span className={`topBarChange topBarChange--${tone}`}>
            {change >= 0 ? "▲" : "▼"} {formatCurrency(Math.abs(change))} ({formatPercent(changePct)})
          </span>
        )}
      </div>
    </div>
  );
};
