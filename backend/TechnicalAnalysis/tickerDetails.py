"""
Ticker reference details (shares outstanding, market cap) from Polygon's
free reference endpoint -- separate from price aggregates, and cached far
longer than price data since this barely changes day to day.
"""
import time

from polygon import RESTClient

from . import loadToken

_CACHE_TTL_SECONDS = 24 * 60 * 60  # shares outstanding rarely changes
_cache: dict[str, tuple[float, dict]] = {}


def get_ticker_details(symbol: str) -> dict:
    """
    Return {'shares_outstanding': int | None, 'market_cap': float | None}
    for a ticker, using Polygon's /v3/reference/tickers/{ticker} endpoint.
    """
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("Ticker symbol cannot be empty")

    now = time.monotonic()
    cached = _cache.get(symbol)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    api_key = loadToken.load_token()
    if not api_key:
        raise EnvironmentError(
            "Set your Polygon API key in the POLYGON_TOKEN environment variable."
        )

    client = RESTClient(api_key)
    details = client.get_ticker_details(symbol)

    result = {
        "shares_outstanding": (
            getattr(details, "share_class_shares_outstanding", None)
            or getattr(details, "weighted_shares_outstanding", None)
        ),
        "market_cap": getattr(details, "market_cap", None),
    }
    _cache[symbol] = (now, result)
    return result


def cache_clear() -> None:
    """Exposed for tests."""
    _cache.clear()
