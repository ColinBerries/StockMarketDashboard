import { configs } from "./configs";

export type MarketTiming = "long" | "flat";
export type OptionOverlay = "sell_strangle" | "hold" | "hedge_only";
export type HurstVeto = "trend_follow" | "reduce" | "neutral";

export interface PortfolioLegs {
  market_timing: MarketTiming;
  long_short_book: {
    long: string[];
    short: string[];
  };
  option_overlay: OptionOverlay;
  hurst_veto: Record<string, HurstVeto>;
  universe: string[];
  universeErrors?: Record<string, string>;
}

export interface ApiError {
  message: "Yikers";
}

export const fetchPortfolioLegs = async (): Promise<
  PortfolioLegs | ApiError
> => {
  const response = await fetch(`${configs.BACKEND}/portfolio/legs`);

  if (response.status !== 200) {
    return { message: "Yikers" };
  }

  return await response.json();
};

export const isPortfolioLegs = (
  response: PortfolioLegs | ApiError,
): response is PortfolioLegs => "market_timing" in response;

export interface MacdSeries {
  macd: number[];
  signal: number[];
  histogram: number[];
}

export interface HurstResult {
  value: number | null;
  regime: "persistent" | "mean_reverting" | "random_walk" | "insufficient_data";
}

export interface CombinedSentiment {
  combined: number | null;
  news: number | null;
  social: number | null;
  newsError: string | null;
  socialError: string | null;
}

export interface TickerDashboard {
  ticker: string;
  dates: string[];
  closes: number[];
  ema20: number[] | null;
  ema50: number[] | null;
  rsi: (number | null)[] | null;
  macd: MacdSeries | null;
  obv: number[] | null;
  ad: number[] | null;
  volume: number[] | null;
  sentiment: CombinedSentiment | null;
  crowdSentiment: number | null;
  tailRisk: number | null;
  hurst: HurstResult | null;
  errors?: Record<string, string>;
}

export interface DashboardError {
  error: string;
}

export const fetchTickerDashboard = async (
  ticker: string,
  signal?: AbortSignal,
): Promise<TickerDashboard | DashboardError> => {
  const response = await fetch(
    `${configs.BACKEND}/dashboard/${encodeURIComponent(ticker)}`,
    { signal },
  );
  const body = await response.json();

  if (response.status !== 200) {
    return { error: body?.error ?? "Yikers" };
  }

  return body as TickerDashboard;
};

export const isTickerDashboard = (
  response: TickerDashboard | DashboardError,
): response is TickerDashboard => "dates" in response;
