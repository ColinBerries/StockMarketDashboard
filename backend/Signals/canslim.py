"""
CANSLIM-inspired screening (William O'Neil / Investor's Business Daily
methodology), built entirely from data this project can access for free.

Honest accounting of coverage -- four of the seven letters are genuinely
computable, three are not:

  N - New highs / breakout        -- computable from price history
  S - Shares outstanding + volume -- computable (Polygon reference data
                                      is free; aggregates give volume)
  L - Leading stocks (RS rating)  -- computable, but ranked against this
                                      project's configured universe, not
                                      the whole market -- an approximation
                                      of IBD's real RS Rating, not the
                                      genuine article
  M - Market conditions           -- approximated via SPY's 50/200-day
                                      moving averages, NOT IBD's
                                      proprietary "Market Posture"
                                      indicator

  C - Current quarterly EPS growth -- UNAVAILABLE. Requires Polygon's
                                       paid Financials/Fundamentals plan.
  A - Annual EPS growth (5yr CAGR) -- UNAVAILABLE. Same as C.
  I - Institutional ownership      -- UNAVAILABLE. No integrated free
                                       source (would require parsing SEC
                                       13F filings directly).

`screen_ticker()`'s `available_criteria_met` reflects ONLY N/S/L/M. It is
NOT a full CANSLIM qualification -- the two earnings-growth screens O'Neil
treated as foundational, plus institutional sponsorship, are not checked
at all here. Every caller (API responses, UI labels) should say "N/S/L/M"
or "4 of 7 criteria", never just "CANSLIM qualified".
"""
import statistics

UNAVAILABLE = "unavailable"


def near_52_week_high(closes: list[float], within_pct: float = 15.0) -> dict:
    """N (partial): is the current close within `within_pct`% of its
    trailing 252-trading-day high?"""
    window = closes[-252:] if len(closes) >= 252 else closes
    if len(window) < 20:
        raise ValueError("Not enough price history for a 52-week-high check")
    high = max(window)
    current = closes[-1]
    pct_below_high = (high - current) / high * 100.0 if high else float("inf")
    return {
        "pass": bool(pct_below_high <= within_pct),
        "pct_below_52wk_high": float(pct_below_high),
        "week_52_high": float(high),
    }


def is_breaking_out(
    closes: list[float],
    volumes: list[float],
    consolidation_window: int = 35,
    max_range_pct: float = 25.0,
    volume_multiplier: float = 1.4,
) -> dict:
    """
    N (partial): a simple breakout proxy for "breaking out of a period of
    consolidation" -- checks that the `consolidation_window` days before
    today traded in a tight range (a "base"), and that today closed at a
    new high on above-average volume. This is a heuristic, not IBD's
    proprietary base-pattern detection (cup-with-handle, flat base, etc).
    """
    if len(closes) < consolidation_window + 2:
        raise ValueError("Not enough price history for a breakout check")

    base_closes = closes[-(consolidation_window + 1):-1]
    base_volumes = volumes[-(consolidation_window + 1):-1]
    base_high, base_low = max(base_closes), min(base_closes)
    base_range_pct = (
        (base_high - base_low) / base_low * 100.0 if base_low else float("inf")
    )

    today_close = closes[-1]
    today_volume = volumes[-1]
    avg_base_volume = (
        statistics.fmean(base_volumes) if len(base_volumes) else 0.0
    )

    tight_base = base_range_pct <= max_range_pct
    new_high_today = today_close >= base_high
    volume_surge = (
        avg_base_volume > 0 and today_volume >= avg_base_volume * volume_multiplier
    )

    return {
        "pass": bool(tight_base and new_high_today and volume_surge),
        "base_range_pct": float(base_range_pct),
        "volume_vs_base_avg": (
            float(today_volume / avg_base_volume) if avg_base_volume else None
        ),
    }


def shares_outstanding_check(
    shares_outstanding: float | None,
    max_shares: float = 50_000_000,
) -> dict:
    """S (partial): shares outstanding under 50 million."""
    if shares_outstanding is None:
        return {"pass": None, "shares_outstanding": None}
    native_shares = float(shares_outstanding)
    return {
        "pass": bool(native_shares < max_shares),
        "shares_outstanding": native_shares,
    }


def volume_increase_check(
    volumes: list[float],
    recent_window: int = 10,
    baseline_window: int = 50,
    multiplier: float = 1.25,
) -> dict:
    """S (partial): a recent increase in trading volume vs. the longer
    baseline average."""
    if len(volumes) < baseline_window + recent_window:
        raise ValueError("Not enough volume history for this check")
    recent = statistics.fmean(volumes[-recent_window:])
    baseline = statistics.fmean(
        volumes[-(baseline_window + recent_window):-recent_window]
    )
    ratio = (recent / baseline) if baseline else None
    return {
        "pass": bool(ratio is not None and ratio >= multiplier),
        "recent_avg_volume": recent,
        "baseline_avg_volume": baseline,
        "volume_ratio": ratio,
    }


def one_year_return(closes: list[float]) -> float:
    window = closes[-252:] if len(closes) >= 252 else closes
    if len(window) < 20 or not window[0]:
        raise ValueError("Not enough price history for a 1-year return")
    return float((window[-1] - window[0]) / window[0])


def relative_strength_rating(ticker: str, one_year_returns: dict[str, float]) -> dict:
    """
    L: percentile rank (0-100) of `ticker`'s 1-year return within
    `one_year_returns` (ticker -> 1-year return, for the configured
    universe). NOTE: ranks against the configured universe, not the whole
    market -- IBD's real RS Rating ranks against the entire market.
    """
    if ticker not in one_year_returns or len(one_year_returns) < 5:
        raise ValueError("Not enough universe data for a relative strength rating")
    values = sorted(one_year_returns.values())
    current = one_year_returns[ticker]
    rank = sum(1 for value in values if value <= current) / len(values) * 100.0
    return {"pass": bool(rank >= 80.0), "rs_rating": float(rank)}


def market_posture(spy_closes: list[float]) -> dict:
    """
    M (approximated): SPY above its 50-day and 200-day simple moving
    averages, with the 50-day above the 200-day -- a standard trend-
    following proxy, NOT IBD's proprietary Market Posture indicator.
    """
    if len(spy_closes) < 200:
        raise ValueError("Not enough SPY history for a 200-day moving average")
    sma50 = statistics.fmean(spy_closes[-50:])
    sma200 = statistics.fmean(spy_closes[-200:])
    current = spy_closes[-1]
    bullish = current > sma50 > sma200
    return {
        "pass": bool(bullish),
        "posture": "Bullish" if bullish else "Bearish",
        "sma50": sma50,
        "sma200": sma200,
    }


def screen_ticker(
    ticker: str,
    closes: list[float],
    volumes: list[float],
    shares_outstanding: float | None,
    one_year_returns: dict[str, float],
    spy_closes: list[float],
) -> dict:
    """
    Run every available CANSLIM-inspired criterion for one ticker.
    C, A, and I are always reported with status "unavailable" -- see the
    module docstring for why.
    """
    results: dict = {}
    errors: dict = {}

    def _safe(key, fn):
        try:
            results[key] = fn()
        except Exception as error:  # noqa: BLE001 - reported per-key, not raised
            results[key] = None
            errors[key] = str(error)

    results["C"] = {"pass": None, "status": UNAVAILABLE}
    results["A"] = {"pass": None, "status": UNAVAILABLE}
    _safe("N_high", lambda: near_52_week_high(closes))
    _safe("N_breakout", lambda: is_breaking_out(closes, volumes))
    _safe("S_shares", lambda: shares_outstanding_check(shares_outstanding))
    _safe("S_volume", lambda: volume_increase_check(volumes))
    _safe("L", lambda: relative_strength_rating(ticker, one_year_returns))
    results["I"] = {"pass": None, "status": UNAVAILABLE}
    _safe("M", lambda: market_posture(spy_closes))

    available_keys = ["N_high", "N_breakout", "S_shares", "S_volume", "L", "M"]
    evaluated = [
        key for key in available_keys
        if results.get(key) is not None and results[key].get("pass") is not None
    ]
    passed = [key for key in evaluated if results[key]["pass"] is True]

    return {
        "ticker": ticker,
        "criteria": results,
        "available_criteria_met": bool(evaluated) and len(passed) == len(evaluated),
        "available_criteria_count": f"{len(passed)}/{len(evaluated)}" if evaluated else "0/0",
        "errors": errors,
    }
