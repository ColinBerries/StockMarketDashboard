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

// --- Monte Carlo portfolio simulation --------------------------------

export type RiskProfile = "conservative" | "moderate" | "aggressive";
export type ReturnDistribution = "gaussian" | "stable";

export interface MonteCarloBand {
  year: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export interface MonteCarloAssumptions {
  annualized_stock_mean: number;
  annualized_stock_std: number;
  stable_alpha: number;
  risk_free_rate: number;
}

export interface MonteCarloResult {
  years: number;
  stock_weight: number;
  distribution: ReturnDistribution;
  n_iterations: number;
  assumptions: MonteCarloAssumptions;
  bands: MonteCarloBand[];
  final_value_percentiles: Record<string, number>;
  target_value?: number;
  probability_of_target?: number;
}

export interface MonteCarloParams {
  initial: number;
  years: number;
  riskProfile?: RiskProfile;
  stockWeight?: number;
  riskFreeRate?: number;
  distribution?: ReturnDistribution;
  iterations?: number;
  target?: number;
}

export interface MonteCarloError {
  error: string;
}

export const fetchMonteCarloSimulation = async (
  params: MonteCarloParams,
  signal?: AbortSignal,
): Promise<MonteCarloResult | MonteCarloError> => {
  const query = new URLSearchParams();
  query.set("initial", String(params.initial));
  query.set("years", String(params.years));
  if (params.riskProfile) query.set("riskProfile", params.riskProfile);
  if (params.stockWeight !== undefined) {
    query.set("stockWeight", String(params.stockWeight));
  }
  if (params.riskFreeRate !== undefined) {
    query.set("riskFreeRate", String(params.riskFreeRate));
  }
  if (params.distribution) {
    query.set("distribution", params.distribution);
  }
  if (params.iterations !== undefined) {
    query.set("iterations", String(params.iterations));
  }
  if (params.target !== undefined) {
    query.set("target", String(params.target));
  }

  const response = await fetch(
    `${configs.BACKEND}/montecarlo/simulate?${query.toString()}`,
    { signal },
  );
  const body = await response.json();
  if (response.status !== 200) {
    return { error: body?.error ?? "Yikers" };
  }
  return body as MonteCarloResult;
};

export const isMonteCarloResult = (
  response: MonteCarloResult | MonteCarloError,
): response is MonteCarloResult => "bands" in response;
