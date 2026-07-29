import datetime as dt
import re
import time
from functools import lru_cache
from pathlib import Path

import pandas as pd
from polygon import RESTClient

from . import loadToken


_DEFAULT_SYMBOL = "AAPL"
_PERIOD_DAYS = 730
_API_KEY_ENV_NAME = "POLYGON_TOKEN"
_CACHE_DIR = Path(__file__).resolve().parent.parent

# Polygon's free tier caps out at 5 requests/minute. Fetching an uncached
# universe of tickers (e.g. for the portfolio-legs view) can burst well past
# that, so a rate-limited request is retried with exponential backoff rather
# than failing immediately.
_RATE_LIMIT_MAX_RETRIES = 4
_RATE_LIMIT_BASE_DELAY_SECONDS = 15.0


def _cache_file(symbol: str) -> Path:
    safe_symbol = re.sub(r"[^A-Z0-9._-]", "_", symbol.upper())
    return _CACHE_DIR / f"price_data_{safe_symbol}.pkl"


def _is_rate_limit_error(error: Exception) -> bool:
    message = str(error)
    return "429" in message or "too many" in message.lower()


def _download_polygon(
    symbol: str,
    start_date: dt.date,
    end_date: dt.date,
    api_key: str,
) -> pd.DataFrame:
    """Download raw daily aggregate bars from Polygon.io, retrying on 429s."""
    client = RESTClient(api_key)

    attempt = 0
    while True:
        try:
            aggs = client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                adjusted=True,
            )
            break
        except Exception as error:
            attempt += 1
            rate_limited = _is_rate_limit_error(error)
            if not rate_limited or attempt > _RATE_LIMIT_MAX_RETRIES:
                if rate_limited:
                    raise RuntimeError(
                        f"Polygon rate limit exceeded for {symbol} after "
                        f"{attempt - 1} retries. Your API plan may be too "
                        "restrictive for the number of tickers being "
                        "fetched at once -- see https://polygon.io/pricing "
                        "for higher-throughput tiers."
                    ) from error
                raise
            delay = _RATE_LIMIT_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            time.sleep(delay)

    if not aggs:
        raise ValueError(
            f"Polygon returned 0 rows for {symbol} "
            f"between {start_date} and {end_date}."
        )

    return (
        pd.DataFrame(
            {
                "open": [aggregate.open for aggregate in aggs],
                "high": [aggregate.high for aggregate in aggs],
                "low": [aggregate.low for aggregate in aggs],
                "close": [aggregate.close for aggregate in aggs],
                "volume": [aggregate.volume for aggregate in aggs],
                "vwap": [aggregate.vwap for aggregate in aggs],
                "ts": [
                    pd.to_datetime(aggregate.timestamp, unit="ms")
                    for aggregate in aggs
                ],
            }
        )
        .set_index("ts")
        .sort_index()
    )


def _read_cache(cache_file: Path, symbol: str) -> pd.DataFrame | None:
    if not cache_file.is_file():
        return None
    try:
        cached = pd.read_pickle(cache_file)
    except (OSError, ValueError, EOFError):
        return None
    if cached.empty or "close" not in cached:
        return None
    cached_symbol = cached.attrs.get("symbol")
    if cached_symbol and cached_symbol != symbol:
        return None
    return cached.sort_index()


@lru_cache(maxsize=32)
def get_price_data(symbol: str = _DEFAULT_SYMBOL) -> pd.DataFrame:
    """
    Return roughly two years of daily Polygon bars for ``symbol``.

    Each ticker has its own on-disk cache. A recent cache is used directly;
    if it is stale and no Polygon token is available, the stale cache is used
    as an offline fallback rather than making package imports fail.
    """
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("Ticker symbol cannot be empty")

    end_date = dt.date.today() + dt.timedelta(days=1)
    start_date = end_date - dt.timedelta(days=_PERIOD_DAYS)
    cache_file = _cache_file(symbol)
    cached = _read_cache(cache_file, symbol)
    api_key = loadToken.load_token()

    if cached is not None:
        has_history = cached.index.min().date() <= start_date
        is_recent = cached.index.max().date() >= dt.date.today() - dt.timedelta(days=7)
        if has_history and is_recent:
            return cached.copy()
        if not api_key:
            return cached.copy()

    if not api_key:
        raise EnvironmentError(
            f"Set your Polygon API key in the {_API_KEY_ENV_NAME} environment variable."
        )

    frame = _download_polygon(symbol, start_date, end_date, api_key)
    frame.attrs["symbol"] = symbol
    frame.to_pickle(cache_file)
    return frame.copy()
