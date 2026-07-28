from dataclasses import dataclass

from .vrp import vrp_zscore


@dataclass
class PortfolioState:
    market_timing: str
    long_short_book: dict[str, list[str]]
    option_overlay: str
    hurst_veto: dict[str, str]


def build_portfolio_state(
    lambda_t_percentile: float,
    firm_tail_ranks: dict[str, float],
    hurst_by_ticker: dict[str, float | None],
    vrp_value: float,
    vrp_history: list[float],
) -> PortfolioState:
    """
    Compose market timing, cross-sectional, volatility, and Hurst signals.

    Tail-risk inputs use the Signals.tail_risk convention: higher lambda means
    a fatter downside tail. The market is held only in the lowest 30% of its
    observed risk range. The short book receives the lowest-risk quintile and
    the long book the highest-risk quintile.
    """
    market_timing = "long" if lambda_t_percentile <= 30 else "flat"

    sorted_tickers = sorted(
        firm_tail_ranks,
        key=lambda ticker: firm_tail_ranks[ticker],
    )
    count = len(sorted_tickers)
    quintile_size = max(count // 5, 1)
    short_leg = sorted_tickers[:quintile_size]
    long_leg = sorted_tickers[-quintile_size:]

    z_score = vrp_zscore(vrp_value, vrp_history)
    option_overlay = (
        "sell_strangle"
        if z_score is not None and z_score > 1.0
        else "hold"
    )

    hurst_veto = {}
    for ticker, value in hurst_by_ticker.items():
        if value is None:
            hurst_veto[ticker] = "neutral"
        elif value > 0.55:
            hurst_veto[ticker] = "trend_follow"
        elif value < 0.45:
            hurst_veto[ticker] = "reduce"
        else:
            hurst_veto[ticker] = "neutral"

    return PortfolioState(
        market_timing=market_timing,
        long_short_book={"long": long_leg, "short": short_leg},
        option_overlay=option_overlay,
        hurst_veto=hurst_veto,
    )
