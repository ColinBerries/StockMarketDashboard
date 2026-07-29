import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import nltk
import pandas as pd
import requests
from dotenv import load_dotenv
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# "Sentiment Analysis" has a space in its directory name, which makes it an
# invalid Python package identifier -- sibling modules in this folder (also
# loaded via importlib by main.py) can't be reached with a normal `from .
# import x`. Add this directory to sys.path so plain `import x` resolves
# them instead.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import stocktwits  # noqa: E402
from _ttl_cache import ttl_cache  # noqa: E402

load_dotenv()
_analyzer = SentimentIntensityAnalyzer()
_stop_words: set[str] | None = None

# Both sources have tight rate limits (NewsAPI free tier: 100 req/day;
# StockTwits public endpoint: ~200 req/hour) relative to how often a ticker
# might get reloaded while browsing, so raw fetches are cached for 15
# minutes rather than re-fetched on every dashboard request.
_SENTIMENT_CACHE_TTL_SECONDS = 15 * 60


def _english_stop_words() -> set[str]:
    global _stop_words
    if _stop_words is None:
        try:
            _stop_words = set(stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            _stop_words = set(stopwords.words("english"))
    return _stop_words


def _preprocess_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    try:
        words = word_tokenize(text)
    except LookupError:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        words = word_tokenize(text)
    stop_words = _english_stop_words()
    words = [
        word
        for word in words
        if word.isalpha() and word.lower() not in stop_words
    ]
    return " ".join(words)


# --- News (NewsAPI) ---------------------------------------------------


@ttl_cache(_SENTIMENT_CACHE_TTL_SECONDS)
def fetch_headlines(
    query: str,
    days_back: int = 28,
    page_size: int = 100,
) -> pd.DataFrame:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise EnvironmentError("Set NEWS_API_KEY in your .env file.")

    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "from": (
                datetime.now() - timedelta(days=days_back)
            ).strftime("%Y-%m-%d"),
            "sortBy": "relevancy",
            "apiKey": api_key,
            "pageSize": page_size,
            "language": "en",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "ok":
        raise RuntimeError(
            f"NewsAPI error: {data.get('message', 'Unknown error')}"
        )

    news = pd.DataFrame(data["articles"])[["publishedAt", "title"]]
    news.columns = ["date", "headline"]
    return news


def score_sentiment(ticker: str, query: str | None = None) -> pd.DataFrame:
    """Return date, headline, cleaned_headline, and sentiment columns."""
    news = fetch_headlines(query or ticker)
    news["cleaned_headline"] = news["headline"].apply(_preprocess_text)
    news["sentiment"] = news["cleaned_headline"].apply(
        lambda text: _analyzer.polarity_scores(text or "")["compound"]
    )
    return news


def average_sentiment(ticker: str, query: str | None = None) -> float:
    """Return one aggregate news sentiment score over the headline lookback."""
    frame = score_sentiment(ticker, query)
    return float(frame["sentiment"].mean()) if not frame.empty else 0.0


# --- Social (StockTwits) ------------------------------------------------


@ttl_cache(_SENTIMENT_CACHE_TTL_SECONDS)
def fetch_social_messages(ticker: str, limit: int = 30):
    return stocktwits.fetch_messages(ticker, limit)


def score_social_sentiment(ticker: str) -> pd.DataFrame:
    """Return body, cleaned_body, sentiment, and sentiment_label columns
    for recent StockTwits messages about a ticker."""
    messages = fetch_social_messages(ticker)
    frame = pd.DataFrame(messages)
    if frame.empty:
        return frame
    frame["cleaned_body"] = frame["body"].apply(
        lambda text: _preprocess_text(stocktwits.clean_social_text(text))
    )
    frame["sentiment"] = frame["cleaned_body"].apply(
        lambda text: _analyzer.polarity_scores(text or "")["compound"]
    )
    return frame


def average_social_sentiment(ticker: str) -> float:
    """Return one aggregate VADER sentiment score over recent StockTwits
    messages."""
    frame = score_social_sentiment(ticker)
    return float(frame["sentiment"].mean()) if not frame.empty else 0.0


def bull_bear_ratio(ticker: str) -> float | None:
    """
    Fraction of recent StockTwits messages self-labeled 'Bullish' among
    those that carry a Bullish/Bearish label at all (unlabeled messages
    are excluded, since most posts aren't tagged). Returns None if no
    message in the fetched batch was labeled.

    This is a different signal from VADER's text-inferred sentiment above
    -- it's the crowd's own self-reported call, not an NLP guess.
    """
    messages = fetch_social_messages(ticker)
    labeled = [m for m in messages if m["sentiment_label"] in ("Bullish", "Bearish")]
    if not labeled:
        return None
    bullish = sum(1 for m in labeled if m["sentiment_label"] == "Bullish")
    return bullish / len(labeled)


# --- Combined -------------------------------------------------------------


def combined_sentiment(
    ticker: str,
    news_weight: float = 0.5,
    social_weight: float = 0.5,
) -> dict:
    """
    Blend NewsAPI headline sentiment and StockTwits social sentiment (both
    VADER-scored) into one combined score. Degrades gracefully: if either
    source is unavailable (missing API key, rate limited, etc.) the
    combined score falls back to whichever source succeeded, with the
    failure reason reported per-source rather than failing the whole call.
    Raises only if *both* sources fail.
    """
    news_value: float | None = None
    social_value: float | None = None
    news_error: str | None = None
    social_error: str | None = None

    try:
        news_value = average_sentiment(ticker)
    except Exception as error:  # noqa: BLE001 - reported per-source, not raised
        news_error = str(error)

    try:
        social_value = average_social_sentiment(ticker)
    except Exception as error:  # noqa: BLE001 - reported per-source, not raised
        social_error = str(error)

    if news_value is None and social_value is None:
        raise RuntimeError(
            f"Both sentiment sources failed -- news: {news_error}; "
            f"social: {social_error}"
        )

    if news_value is not None and social_value is not None:
        total_weight = news_weight + social_weight
        combined = (
            news_value * news_weight + social_value * social_weight
        ) / total_weight
    else:
        combined = news_value if news_value is not None else social_value

    return {
        "combined": combined,
        "news": news_value,
        "social": social_value,
        "newsError": news_error,
        "socialError": social_error,
    }


if __name__ == "__main__":
    ticker = input("Enter ticker symbol (e.g., NVDA): ").upper().strip()
    result = combined_sentiment(ticker)
    print(f"Combined sentiment for {ticker}: {result['combined']:.3f}")
    print(f"  news:   {result['news']}")
    print(f"  social: {result['social']}")
    ratio = bull_bear_ratio(ticker)
    print(f"  crowd bullish ratio: {ratio}")
