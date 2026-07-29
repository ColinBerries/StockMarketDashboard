"""
StockTwits integration: fetches recent public messages for a ticker.

Uses StockTwits' public, unauthenticated symbol-stream endpoint
(https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json). This is
read-only and requires no API key, but StockTwits rate-limits it to
roughly 200 requests/hour per IP -- results are cached at the sentiment.py
layer (via _ttl_cache) to stay well under that.
"""
import re
from typing import TypedDict

import requests

_BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
_USER_AGENT = (
    "StockMarketDashboard/1.0 "
    "(+https://github.com/ColinBerries/StockMarketDashboard)"
)
_REQUEST_TIMEOUT_SECONDS = 15


class StockTwitsMessage(TypedDict):
    body: str
    sentiment_label: str | None  # "Bullish", "Bearish", or None


def fetch_messages(ticker: str, limit: int = 30) -> list[StockTwitsMessage]:
    """Fetch the most recent public messages for a ticker's symbol stream."""
    symbol = ticker.upper().strip()
    if not symbol:
        raise ValueError("Ticker symbol cannot be empty")

    response = requests.get(
        _BASE_URL.format(symbol=symbol),
        headers={"User-Agent": _USER_AGENT},
        timeout=_REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 429:
        raise RuntimeError(
            "StockTwits rate limit exceeded (the public endpoint allows "
            "roughly 200 requests/hour per IP). Try again shortly."
        )
    response.raise_for_status()

    payload = response.json()
    if payload.get("response", {}).get("status") != 200:
        raise RuntimeError(
            f"StockTwits error for {symbol}: "
            f"{payload.get('errors', 'unknown error')}"
        )

    raw_messages = payload.get("messages", [])[:limit]
    messages: list[StockTwitsMessage] = []
    for raw in raw_messages:
        body = raw.get("body", "")
        sentiment_entity = (raw.get("entities") or {}).get("sentiment") or {}
        label = sentiment_entity.get("basic")  # "Bullish" | "Bearish" | None
        messages.append({"body": body, "sentiment_label": label})
    return messages


def clean_social_text(text: str) -> str:
    """Strip cashtags, @mentions, and URLs before sentiment scoring."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[$@]\w+", "", text)
    return text.strip()
