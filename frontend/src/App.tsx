import React, { useEffect, useState } from "react";
import "./App.css";
import TickerPull from "./TickerPull";
import EMAPull from "./EMAPull";
import { TickerSelect } from "./tickerSelect/TickerSelect";
import { TopBar } from "./TopBar";
import {
  fetchPortfolioLegs,
  isPortfolioLegs,
  PortfolioLegs,
} from "./lib/api";
import { MarketTimingCard } from "./signals/MarketTimingCard";
import { LongShortTable } from "./signals/LongShortTable";
import { OptionOverlayCard } from "./signals/OptionOverlayCard";

function App() {
  const [price, setPrice] = useState("0");
  const [emaPrice, setEmaPrice] = useState("0");
  const [portfolioLegs, setPortfolioLegs] = useState<PortfolioLegs | null>(
    null,
  );
  const [portfolioError, setPortfolioError] = useState(false);
  const [activeTicker, setActiveTicker] = useState<{
    name: string;
    ticker: string;
  }>({
    name: "Apple Inc.",
    ticker: "AAPL",
  });

  useEffect(() => {
    let active = true;
    fetchPortfolioLegs()
      .then((response) => {
        if (!active) {
          return;
        }
        if (isPortfolioLegs(response)) {
          setPortfolioLegs(response);
          setPortfolioError(false);
        } else {
          setPortfolioError(true);
        }
      })
      .catch(() => {
        if (active) {
          setPortfolioError(true);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="App">
      <div className="left">
        <TopBar activeTicker={activeTicker} />
        <div className="content">
          <TickerPull ticker={activeTicker.ticker} setPrice={setPrice} />
          <EMAPull ticker={activeTicker.ticker} setPrice={setEmaPrice} />

          <main>
            <section id="closingPrice" className="enhanced-section">
              <h2>Closing Price</h2>
              <p>
                <span id="ticker-pull">{price}</span>
              </p>
            </section>
            <section id="ema" className="enhanced-section">
              <h2>Exponential Moving Average (EMA)</h2>
              <p>
                <span>{emaPrice}</span>
              </p>
            </section>
            {portfolioLegs && (
              <div className="signalDashboard">
                <MarketTimingCard state={portfolioLegs.market_timing} />
                <LongShortTable book={portfolioLegs.long_short_book} />
                <OptionOverlayCard state={portfolioLegs.option_overlay} />
              </div>
            )}
            {portfolioError && (
              <p className="signalError">Portfolio signals are unavailable.</p>
            )}
          </main>
        </div>
      </div>
      <div className="right">
        <TickerSelect
          setActiveTicker={setActiveTicker}
          hurstVeto={portfolioLegs?.hurst_veto ?? {}}
        />
      </div>
    </div>
  );
}

export default App;
