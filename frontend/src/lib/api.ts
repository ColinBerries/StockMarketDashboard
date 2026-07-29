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

// --- CANSLIM screening ------------------------------------------------
//
// C (current quarterly EPS growth) and A (annual EPS growth) are always
// "unavailable" -- they need Polygon's paid Financials add-on, which
// this project doesn't have. I (institutional ownership) is always
// "unavailable" too -- no integrated free data source. See
// backend/Signals/canslim.py for the full explanation. Treat
// `available_criteria_met` as "met N/S/L/M", never as full CANSLIM
// qualification.

export interface CanslimUnavailableCriterion {
  pass: null;
  status: "unavailable";
}

export interface CanslimNumericCriterion {
  pass: boolean;
  [key: string]: number | boolean | null;
}

export type CanslimCriterion = CanslimUnavailableCriterion | CanslimNumericCriterion | null;

export interface CanslimResult {
  ticker: string;
  criteria: {
    C: CanslimUnavailableCriterion;
    A: CanslimUnavailableCriterion;
    N_high: CanslimCriterion;
    N_breakout: CanslimCriterion;
    S_shares: CanslimCriterion;
    S_volume: CanslimCriterion;
    L: CanslimCriterion;
    I: CanslimUnavailableCriterion;
    M: CanslimCriterion;
  };
  available_criteria_met: boolean;
  available_criteria_count: string;
  errors: Record<string, string>;
}

export interface CanslimScreenResponse {
  universe: string[];
  results: CanslimResult[];
  universeErrors?: Record<string, string>;
}

export interface CanslimError {
  error: string;
}

export const fetchCanslimScreen = async (): Promise<CanslimScreenResponse | CanslimError> => {
  const response = await fetch(`${configs.BACKEND}/canslim/screen`);
  const body = await response.json();
  if (response.status !== 200) {
    return { error: body?.error ?? "Yikers" };
  }
  return body as CanslimScreenResponse;
};

export const isCanslimScreenResponse = (
  response: CanslimScreenResponse | CanslimError,
): response is CanslimScreenResponse => "results" in response;

export const fetchCanslimTicker = async (
  ticker: string,
  signal?: AbortSignal,
): Promise<CanslimResult | CanslimError> => {
  const response = await fetch(
    `${configs.BACKEND}/canslim/${encodeURIComponent(ticker)}`,
    { signal },
  );
  const body = await response.json();
  if (response.status !== 200) {
    return { error: body?.error ?? "Yikers" };
  }
  return body as CanslimResult;
};

export const isCanslimResult = (
  response: CanslimResult | CanslimError,
): response is CanslimResult => "criteria" in response;
