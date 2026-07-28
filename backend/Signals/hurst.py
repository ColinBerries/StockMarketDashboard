import numpy as np


def rescaled_range_hurst(series: list[float]) -> float:
    """
    Return a single-window R/S Hurst estimate based on log returns.
    """
    prices = np.asarray(series, dtype=float)
    if np.any(prices <= 0):
        raise ValueError("Prices must be positive")

    log_returns = np.diff(np.log(prices))
    n = len(log_returns)
    if n < 8:
        raise ValueError("Need at least 8 return observations")

    mean_adjusted = log_returns - log_returns.mean()
    cumulative = np.cumsum(mean_adjusted)
    r = cumulative.max() - cumulative.min()
    s = log_returns.std(ddof=1)
    if s == 0:
        return 0.5
    rs = r / s
    if rs <= 0:
        return 0.5
    return float(np.log(rs) / np.log(n))


def moving_hurst(
    closes: list[float],
    window: int = 32,
) -> list[float | None]:
    """
    Return rolling Hurst estimates aligned to the close-price series.
    """
    if window < 9:
        raise ValueError("window must contain at least 9 prices")

    result: list[float | None] = [None] * len(closes)
    for index in range(window, len(closes) + 1):
        segment = closes[index - window : index]
        try:
            result[index - 1] = rescaled_range_hurst(segment)
        except ValueError:
            result[index - 1] = None
    return result


def hurst_regime(h: float | None) -> str:
    if h is None:
        return "insufficient_data"
    if h > 0.55:
        return "persistent"
    if h < 0.45:
        return "mean_reverting"
    return "random_walk"


def moving_hurst_dual(
    closes: list[float],
    fast: int = 16,
    slow: int = 32,
) -> tuple[list[float | None], list[float | None]]:
    """Return aligned fast- and slow-window Hurst series."""
    return moving_hurst(closes, fast), moving_hurst(closes, slow)
