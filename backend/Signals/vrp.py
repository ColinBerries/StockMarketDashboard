"""
Volatility-risk-premium calculations.

This module expects an annualized one-month ATM implied-volatility input.
It does not substitute realized volatility for implied volatility, because
that would not be a real VRP signal.
"""

import numpy as np


def realized_vol(
    closes: list[float],
    window: int = 21,
    annualize: bool = True,
) -> float:
    """Return trailing realized volatility over ``window`` trading days."""
    if window < 2:
        raise ValueError("window must be at least 2")
    if len(closes) < window + 1:
        raise ValueError(
            f"Need at least {window + 1} closes for a {window}-day window"
        )

    prices = np.asarray(closes[-(window + 1) :], dtype=float)
    if np.any(prices <= 0):
        raise ValueError("Close prices must be positive")
    log_returns = np.diff(np.log(prices))
    volatility = log_returns.std(ddof=1)
    if annualize:
        volatility *= np.sqrt(252)
    return float(volatility)


def vrp(
    implied_vol_1m: float,
    closes: list[float],
    realized_window: int = 21,
) -> float:
    """
    Return one-month ATM implied volatility minus trailing realized volatility.
    """
    if implied_vol_1m < 0:
        raise ValueError("implied_vol_1m cannot be negative")
    rv = realized_vol(closes, window=realized_window)
    return float(implied_vol_1m - rv)


def vrp_zscore(
    current_vrp: float,
    vrp_history: list[float],
) -> float | None:
    """Compare current VRP with prior observations; return None if unavailable."""
    if len(vrp_history) < 2:
        return None
    history = np.asarray(vrp_history, dtype=float)
    standard_deviation = history.std(ddof=1)
    if standard_deviation == 0:
        return None
    return float((current_vrp - history.mean()) / standard_deviation)
