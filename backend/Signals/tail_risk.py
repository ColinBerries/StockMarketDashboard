"""
Downside-tail estimators used by the portfolio signals.

``hill_estimator`` returns the conventional Pareto tail index ``alpha``:
lower alpha means a fatter, riskier tail. Public ``market_tail_risk`` and
``firm_tail_risk`` return ``lambda = 1 / alpha`` so every portfolio consumer
uses one consistent convention: higher lambda means higher tail risk.
"""

import math


def hill_estimator(losses: list[float], k: int) -> float:
    """
    Estimate the Pareto tail index alpha from the ``k`` largest losses.

    Losses are positive numbers where larger values are worse.
    """
    if k >= len(losses) or k < 2:
        raise ValueError("k must be between 2 and len(losses) - 1")

    sorted_losses = sorted(losses, reverse=True)
    threshold = sorted_losses[k]
    if threshold <= 0:
        raise ValueError(
            "Threshold loss must be positive; check input sign convention"
        )

    log_ratios = [
        math.log(sorted_losses[index] / threshold)
        for index in range(k)
    ]
    h_k = sum(log_ratios) / k
    if h_k <= 0:
        raise ValueError("Largest losses must not all equal the threshold")
    return 1.0 / h_k


def daily_losses_from_closes(closes: list[float]) -> list[float]:
    """Convert closes into daily losses, where positive values are down days."""
    losses = []
    for index in range(1, len(closes)):
        previous = closes[index - 1]
        if previous <= 0:
            raise ValueError("Close prices must be positive")
        daily_return = (closes[index] - previous) / previous
        losses.append(max(-daily_return, 1e-9))
    return losses


def market_tail_risk(index_closes: list[float], k: int = 30) -> float:
    """Return lambda_t, the inverse Hill alpha for a market index proxy."""
    losses = daily_losses_from_closes(index_closes)
    alpha_hat = hill_estimator(losses, k)
    return 1.0 / alpha_hat


def firm_tail_risk(
    ticker_closes: dict[str, list[float]],
    k: int = 20,
) -> dict[str, float]:
    """Return per-ticker inverse Hill alpha values (lambda_i)."""
    result = {}
    for ticker, closes in ticker_closes.items():
        losses = daily_losses_from_closes(closes)
        if len(losses) > k:
            alpha_hat = hill_estimator(losses, k)
            result[ticker] = 1.0 / alpha_hat
    return result
