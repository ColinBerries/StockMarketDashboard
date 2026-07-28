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
