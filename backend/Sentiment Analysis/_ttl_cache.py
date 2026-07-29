"""
A minimal in-memory TTL cache.

functools.lru_cache has no expiry, which is fine for Polygon price bars
(handled separately, with its own disk cache) but wrong for sentiment: news
and social results should refresh periodically, and both NewsAPI's free
tier (100 requests/day) and StockTwits' public endpoint (~200 requests/hour)
are far too tight to re-fetch on every ticker click without caching.
"""
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def ttl_cache(ttl_seconds: float):
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        store: dict[tuple, tuple[float, T]] = {}

        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            if key in store:
                cached_at, value = store[key]
                if now - cached_at < ttl_seconds:
                    return value
            value = fn(*args, **kwargs)
            store[key] = (now, value)
            return value

        wrapper.cache_clear = store.clear  # exposed for tests
        return wrapper

    return decorator
