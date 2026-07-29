import { useEffect, useState } from "react";
import "./App.css";
import { TickerSelect } from "./tickerSelect/TickerSelect";
import { TopBar } from "./TopBar";
import { fetchPortfolioLegs, isPortfolioLegs, PortfolioLegs } from "./lib/api";
import { MarketTimingCard } from "./signals/MarketTimingCard";
import { LongShortTable } from "./signals/LongShortTable";
import { OptionOverlayCard } from "./signals/OptionOverlayCard";
import { UniverseList } from "./signals/UniverseList";
import { useTickerDashboard } from "./hooks/useTickerDashboard";
import { ChartCard } from "./charts/ChartCard";
import { IndicatorChart } from "./charts/IndicatorChart";
import { MacdChart } from "./charts/MacdChart";
import { VolumeChart } from "./charts/VolumeChart";
import { StatBadge, BadgeTone } from "./components/StatBadge";
import { alignRight, formatNumber } from "./lib/format";

function App() {
  const [portfolioLegs, setPortfolioLegs] = useState<PortfolioLegs | null>(null);
  const [portfolioError, setPortfolioError] = useState(false);
  const [activeTicker, setActiveTicker] = useState<{ name: string; ticker: string }>({
    name: "Apple Inc.",
    ticker: "AAPL",
  });

  const { data: dashboard, error: dashboardError, loading } = useTickerDashboard(
    activeTicker.ticker,
  );

  useEffect(() => {
    let active = true;
    fetchPortfolioLegs()
      .then((response) => {
        if (!active) return;
        if (isPortfolioLegs(response)) {
          setPortfolioLegs(response);
          setPortfolioError(false);
        } else {
          setPortfolioError(true);
        }
      })
      .catch(() => {
        if (active) setPortfolioError(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const dates = dashboard?.dates ?? [];
  const n = dates.length;
  const closes = dashboard?.closes ?? [];
  const ema20Aligned = alignRight(n, dashboard?.ema20);
  const ema50Aligned = alignRight(n, dashboard?.ema50);

  const priceData = dates.map((date, i) => ({
    date,
    close: closes[i] ?? null,
    ema20: ema20Aligned[i],
    ema50: ema50Aligned[i],
  }));

  const rsiData = dates.map((date, i) => ({ date, rsi: dashboard?.rsi?.[i] ?? null }));

  const macdData = dates.map((date, i) => ({
    date,
    macd: dashboard?.macd?.macd[i] ?? null,
    signal: dashboard?.macd?.signal[i] ?? null,
    histogram: dashboard?.macd?.histogram[i] ?? null,
  }));

  const obvData = dates.map((date, i) => ({ date, obv: dashboard?.obv?.[i] ?? null }));
  const adData = dates.map((date, i) => ({ date, ad: dashboard?.ad?.[i] ?? null }));
  const volumeData = dates.map((date, i) => ({ date, volume: dashboard?.volume?.[i] ?? null }));

  const lastClose = closes.length > 0 ? closes[closes.length - 1] : null;
  const prevClose = closes.length > 1 ? closes[closes.length - 2] : null;
  const change = lastClose !== null && prevClose !== null ? lastClose - prevClose : null;
  const changePct = change !== null && prevClose ? (change / prevClose) * 100 : null;

  const hurstTone: BadgeTone =
    dashboard?.hurst?.regime === "persistent"
      ? "positive"
      : dashboard?.hurst?.regime === "mean_reverting"
        ? "negative"
        : "neutral";

  const sentimentValue = dashboard?.sentiment?.combined ?? null;
  const sentimentTone: BadgeTone =
    sentimentValue === null ? "neutral" : sentimentValue > 0.05 ? "positive" : sentimentValue < -0.05 ? "negative" : "neutral";
  const sentimentDetail =
    dashboard?.sentiment && (dashboard.sentiment.news !== null || dashboard.sentiment.social !== null)
      ? `news ${formatNumber(dashboard.sentiment.news, 2)} · social ${formatNumber(dashboard.sentiment.social, 2)}`
      : undefined;

  const crowdValue = dashboard?.crowdSentiment ?? null;
  const crowdTone: BadgeTone =
    crowdValue === null ? "neutral" : crowdValue > 0.55 ? "positive" : crowdValue < 0.45 ? "negative" : "neutral";
  const crowdDetail = crowdValue === null ? undefined : `${Math.round(crowdValue * 100)}% bullish (StockTwits)`;

  const tailRiskValue = dashboard?.tailRisk ?? null;
  const tailRiskTone: BadgeTone = tailRiskValue !== null && tailRiskValue < 2 ? "negative" : "neutral";

  return (
    <div className="App">
      <div className="left">
        <TopBar activeTicker={activeTicker} price={lastClose} change={change} changePct={changePct} />
        <div className="content">
          <main>
            {portfolioLegs && (
              <div className="signalDashboard">
                <MarketTimingCard state={portfolioLegs.market_timing} />
                <LongShortTable book={portfolioLegs.long_short_book} />
                <OptionOverlayCard state={portfolioLegs.option_overlay} />
                <UniverseList
                  universe={portfolioLegs.universe}
                  book={portfolioLegs.long_short_book}
                  universeErrors={portfolioLegs.universeErrors}
                />
              </div>
            )}
            {portfolioError && <p className="signalError">Portfolio signals are unavailable.</p>}

            {loading && !dashboard && <p className="loadingText">Loading {activeTicker.ticker}…</p>}
            {dashboardError && <p className="signalError">{dashboardError}</p>}

            {dashboard && (
              <>
                <div className="chartGrid chartGridWide">
                  <ChartCard title="Close price + EMA 20 / 50">
                    <IndicatorChart
                      data={priceData}
                      series={[
                        { key: "close", label: "Close", color: "var(--text)" },
                        { key: "ema20", label: "EMA 20", color: "var(--accent)" },
                        { key: "ema50", label: "EMA 50", color: "var(--negative)", dashed: true },
                      ]}
                      height={220}
                    />
                  </ChartCard>
                </div>

                <div className="statRow">
                  <StatBadge
                    label="Sentiment"
                    value={formatNumber(sentimentValue, 2)}
                    detail={sentimentDetail}
                    tone={sentimentTone}
                    error={dashboard.errors?.sentiment}
                  />
                  <StatBadge
                    label="Crowd (StockTwits)"
                    value={crowdValue === null ? "—" : `${Math.round(crowdValue * 100)}%`}
                    detail={crowdDetail}
                    tone={crowdTone}
                    error={dashboard.errors?.crowdSentiment}
                  />
                  <StatBadge
                    label="Tail risk (alpha)"
                    value={formatNumber(tailRiskValue, 2)}
                    detail={
                      tailRiskValue === null
                        ? undefined
                        : tailRiskValue < 2
                          ? "fatter than Gaussian"
                          : "near-Gaussian tail"
                    }
                    tone={tailRiskTone}
                    error={dashboard.errors?.tailRisk}
                  />
                  <StatBadge
                    label="Hurst (32d)"
                    value={formatNumber(dashboard.hurst?.value ?? null, 2)}
                    detail={dashboard.hurst?.regime?.replace("_", " ")}
                    tone={hurstTone}
                    error={dashboard.errors?.hurst}
                  />
                </div>

                <div className="chartGrid">
                  <ChartCard title="RSI (14)" error={dashboard.errors?.rsi}>
                    <IndicatorChart
                      data={rsiData}
                      series={[{ key: "rsi", label: "RSI", color: "var(--accent)" }]}
                      referenceLines={[30, 70]}
                    />
                  </ChartCard>
                  <ChartCard title="MACD (12, 26, 9)" error={dashboard.errors?.macd}>
                    <MacdChart data={macdData} />
                  </ChartCard>
                  <ChartCard title="On-balance volume" error={dashboard.errors?.obv}>
                    <IndicatorChart data={obvData} series={[{ key: "obv", label: "OBV", color: "var(--positive)" }]} />
                  </ChartCard>
                  <ChartCard title="Accumulation / distribution" error={dashboard.errors?.ad}>
                    <IndicatorChart data={adData} series={[{ key: "ad", label: "A/D", color: "var(--accent)" }]} />
                  </ChartCard>
                  <ChartCard title="Volume" error={dashboard.errors?.volume}>
                    <VolumeChart data={volumeData} />
                  </ChartCard>
                </div>
              </>
            )}
          </main>
        </div>
      </div>
      <div className="right">
        <TickerSelect setActiveTicker={setActiveTicker} hurstVeto={portfolioLegs?.hurst_veto ?? {}} />
      </div>
    </div>
  );
}

export default App;
