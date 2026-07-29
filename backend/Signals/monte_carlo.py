"""
Monte Carlo portfolio projector.

Simulates the range of outcomes for a two-asset portfolio (equities +
risk-free) over a multi-year horizon, given a starting amount and a risk
level (stock/risk-free split). Two return models are supported:

  - "gaussian": daily stock returns drawn from a Normal distribution.
  - "stable": daily stock returns drawn from a fitted Levy alpha-stable
    distribution -- fat left tail, so crash days show up far more often
    than a Gaussian model predicts. This is the same fat-tail concept
    from the Fractal Geometry research this project started from: at
    alpha < 2, "risk" in the Markowitz/Gaussian sense understates the
    odds of a bad stretch.

Equity return statistics (daily mean/std, and the tail index for the
"stable" mode) are estimated from this project's own historical SPY
data -- reusing the exact same Hill estimator as the tail-risk portfolio
signal (Signals/tail_risk.py) -- rather than hardcoded constants. Fitting
a full 4-parameter stable distribution via MLE is too slow to run inside
a request (see the earlier research script in this project -- tens of
seconds for a few hundred points); the Hill estimator is fast and reuses
already-tested code, so that's what estimates alpha here.
"""
import statistics
from dataclasses import dataclass

import numpy as np
from scipy.stats import levy_stable, norm

from . import tail_risk

TRADING_DAYS_PER_YEAR = 252

RISK_PROFILES = {
    "conservative": 0.2,
    "moderate": 0.5,
    "aggressive": 0.8,
}

# Worst case (stable distribution, max years * max iterations) takes on the
# order of 10-15 seconds -- these bounds keep a single request within that.
MAX_YEARS = 30
MIN_YEARS = 1
MAX_ITERATIONS = 1500
MIN_ITERATIONS = 100


@dataclass
class MarketAssumptions:
    daily_mean: float
    daily_std: float
    stable_alpha: float  # via the existing Hill estimator; capped at 2.0 (Gaussian-equivalent)


def fit_market_assumptions(closes: list[float], hill_k: int = 30) -> MarketAssumptions:
    """
    Derive daily-return statistics from real historical closes (SPY, by
    convention), and a tail index via the same Hill estimator used by
    the tail-risk portfolio signal.
    """
    if len(closes) < 100:
        raise ValueError("Need at least 100 daily closes to fit market assumptions")

    daily_returns = [
        (closes[index] - closes[index - 1]) / closes[index - 1]
        for index in range(1, len(closes))
        if closes[index - 1]
    ]
    if len(daily_returns) < 50:
        raise ValueError("Not enough valid daily returns to fit market assumptions")

    daily_mean = statistics.fmean(daily_returns)
    daily_std = statistics.pstdev(daily_returns)

    losses = tail_risk.daily_losses_from_closes(closes)
    k = min(hill_k, max(len(losses) - 2, 2))
    try:
        alpha = tail_risk.hill_estimator(losses, k) if len(losses) > k else 2.0
    except ValueError:
        alpha = 2.0
    alpha = min(alpha, 2.0)  # alpha cannot exceed 2 for a valid stable distribution

    return MarketAssumptions(daily_mean=daily_mean, daily_std=daily_std, stable_alpha=alpha)


def _stable_scale_for_std(alpha: float, target_std: float) -> float:
    """
    Alpha-stable distributions with alpha < 2 have infinite variance, so
    there's no `scale` that directly matches a target standard deviation.
    Instead, match the interquartile range (IQR) -- a dispersion measure
    that stays finite for any alpha -- to the IQR a Gaussian with
    `target_std` would have.
    """
    if alpha >= 2.0:
        return target_std
    gaussian_iqr = 2 * norm.ppf(0.75) * target_std  # ~1.349 * std
    standard_stable_iqr = (
        levy_stable.ppf(0.75, alpha, 0.0) - levy_stable.ppf(0.25, alpha, 0.0)
    )
    if standard_stable_iqr <= 0:
        return target_std
    return gaussian_iqr / standard_stable_iqr


def simulate_paths(
    initial_value: float,
    years: int,
    stock_weight: float,
    risk_free_rate: float,
    market: MarketAssumptions,
    distribution: str = "gaussian",
    n_iterations: int = 500,
    random_seed: int | None = None,
) -> np.ndarray:
    """
    Simulate `n_iterations` independent portfolio paths over `years`
    years. Returns an (n_iterations, years + 1) array; column 0 is the
    initial value, column y is the value at the end of year y.
    """
    total_days = years * TRADING_DAYS_PER_YEAR
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    rng = np.random.default_rng(random_seed)

    if distribution == "stable":
        scale = _stable_scale_for_std(market.stable_alpha, market.daily_std)
        stock_returns = levy_stable.rvs(
            market.stable_alpha, 0.0,
            loc=market.daily_mean, scale=scale,
            size=(n_iterations, total_days),
            random_state=rng,
        )
    else:
        stock_returns = rng.normal(
            market.daily_mean, market.daily_std, size=(n_iterations, total_days)
        )

    daily_returns = stock_weight * stock_returns + (1 - stock_weight) * daily_rf
    cumulative_growth = np.cumprod(1 + daily_returns, axis=1)

    year_end_indices = [TRADING_DAYS_PER_YEAR * year - 1 for year in range(1, years + 1)]
    year_end_values = initial_value * cumulative_growth[:, year_end_indices]

    return np.concatenate(
        [np.full((n_iterations, 1), initial_value), year_end_values], axis=1
    )


def run_simulation(
    initial_value: float,
    years: int,
    spy_closes: list[float],
    risk_profile: str | None = None,
    stock_weight: float | None = None,
    risk_free_rate: float = 0.03,
    distribution: str = "gaussian",
    n_iterations: int = 500,
    target_value: float | None = None,
    random_seed: int | None = None,
) -> dict:
    if stock_weight is None:
        if risk_profile not in RISK_PROFILES:
            raise ValueError(
                f"risk_profile must be one of {list(RISK_PROFILES)}, "
                "or pass stock_weight directly"
            )
        stock_weight = RISK_PROFILES[risk_profile]
    if not 0.0 <= stock_weight <= 1.0:
        raise ValueError("stock_weight must be between 0 and 1")
    if distribution not in ("gaussian", "stable"):
        raise ValueError('distribution must be "gaussian" or "stable"')
    if not MIN_YEARS <= years <= MAX_YEARS:
        raise ValueError(f"years must be between {MIN_YEARS} and {MAX_YEARS}")
    if not MIN_ITERATIONS <= n_iterations <= MAX_ITERATIONS:
        raise ValueError(
            f"n_iterations must be between {MIN_ITERATIONS} and {MAX_ITERATIONS}"
        )
    if initial_value <= 0:
        raise ValueError("initial_value must be positive")

    market = fit_market_assumptions(spy_closes)
    paths = simulate_paths(
        initial_value, years, stock_weight, risk_free_rate, market,
        distribution, n_iterations, random_seed,
    )

    percentiles = (5, 25, 50, 75, 95)
    bands = [
        {
            "year": year,
            **{f"p{p}": float(np.percentile(paths[:, year], p)) for p in percentiles},
        }
        for year in range(paths.shape[1])
    ]

    final_values = paths[:, -1]
    result: dict = {
        "years": int(years),
        "stock_weight": float(stock_weight),
        "distribution": distribution,
        "n_iterations": int(n_iterations),
        "assumptions": {
            "annualized_stock_mean": float(
                (1 + market.daily_mean) ** TRADING_DAYS_PER_YEAR - 1
            ),
            "annualized_stock_std": float(market.daily_std * (TRADING_DAYS_PER_YEAR ** 0.5)),
            "stable_alpha": float(market.stable_alpha),
            "risk_free_rate": float(risk_free_rate),
        },
        "bands": bands,
        "final_value_percentiles": {
            f"p{p}": float(np.percentile(final_values, p))
            for p in (5, 10, 25, 50, 75, 90, 95)
        },
    }
    if target_value is not None:
        if target_value <= 0:
            raise ValueError("target_value must be positive")
        result["target_value"] = float(target_value)
        result["probability_of_target"] = float(np.mean(final_values >= target_value))
    return result
