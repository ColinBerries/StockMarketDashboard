import os
from datetime import datetime, timedelta

import nltk
import pandas as pd
import requests
from dotenv import load_dotenv
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


load_dotenv()
_analyzer = SentimentIntensityAnalyzer()
_stop_words: set[str] | None = None


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
    """Return one aggregate sentiment score over the headline lookback."""
    frame = score_sentiment(ticker, query)
    return float(frame["sentiment"].mean()) if not frame.empty else 0.0


if __name__ == "__main__":
    ticker = input("Enter ticker symbol (e.g., NVDA): ").upper().strip()
    print(f"Average sentiment for {ticker}: {average_sentiment(ticker):.3f}")
