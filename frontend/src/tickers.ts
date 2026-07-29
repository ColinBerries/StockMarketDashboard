// A local, curated list of tickers shown by default and matched against as
// you type. This is only for the click-to-browse convenience list — it is
// NOT a limit on what you can load. Type any symbol and press Enter (see
// TickerSelect.tsx) to load a ticker that isn't in this list at all.
export const tickers: Record<
  string,
  {
    companyName: string;
    icon?: string;
  }
> = {
  AAPL: { companyName: "Apple", icon: "https://assets.fey.com/logos/AAPL_XNAS.svg" },
  MSFT: { companyName: "Microsoft", icon: "https://assets.fey.com/logos/MSFT_XNAS.svg" },
  NVDA: { companyName: "Nvidia", icon: "https://assets.fey.com/logos/NVDA_XNAS.svg" },
  AMZN: { companyName: "Amazon", icon: "https://assets.fey.com/logos/AMZN_XNAS.svg" },
  GOOGL: { companyName: "Alphabet Class A", icon: "https://assets.fey.com/logos/GOOGL_XNAS.svg" },
  GOOG: { companyName: "Alphabet Class C", icon: "https://assets.fey.com/logos/GOOG_XNAS.svg" },
  META: { companyName: "Meta Platforms", icon: "https://assets.fey.com/logos/META_XNAS.svg" },
  TSLA: { companyName: "Tesla", icon: "https://assets.fey.com/logos/TSLA_XNAS.svg" },
  JPM: { companyName: "JPMorgan Chase", icon: "https://assets.fey.com/logos/JPM_XNYS.svg" },
  NFLX: { companyName: "Netflix", icon: "https://assets.fey.com/logos/NFLX_XNAS.svg" },
  AMD: { companyName: "Advanced Micro Devices", icon: "https://assets.fey.com/logos/AMD_XNAS.svg" },
  DIS: { companyName: "Walt Disney", icon: "https://assets.fey.com/logos/DIS_XNYS.svg" },
  CMG: { companyName: "Chipotle", icon: "https://assets.fey.com/logos/CMG_XNYS.svg" },
  RBLX: { companyName: "Roblox", icon: "https://assets.fey.com/logos/RBLX_XNYS.svg" },
  SPY: { companyName: "S&P 500 ETF" },
  FLYY: { companyName: "Spirit Aviation Holdings" },
};
