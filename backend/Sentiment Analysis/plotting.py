from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


def plot_price_vs_sentiment(
    ticker: str,
    sentiment: pd.DataFrame,
    days_back: int = 28,
) -> None:
    """Plot closing prices and daily aggregate sentiment on shared dates."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    prices = yf.Ticker(ticker).history(start=start_date, end=end_date)
    prices = prices.reset_index()[["Date", "Close"]]
    prices["date"] = pd.to_datetime(prices["Date"]).dt.date

    scored = sentiment.copy()
    scored["date"] = pd.to_datetime(scored["date"]).dt.date
    daily = scored.groupby("date", as_index=False)["sentiment"].sum()
    combined = prices.merge(daily, on="date", how="left")
    combined["sentiment"] = combined["sentiment"].fillna(0.0)

    figure, price_axis = plt.subplots(figsize=(14, 7))
    price_axis.set_xlabel("Date")
    price_axis.set_ylabel(f"{ticker.upper()} closing price")
    price_axis.plot(combined["date"], combined["Close"], linewidth=2.2)

    sentiment_axis = price_axis.twinx()
    sentiment_axis.set_ylabel("Aggregated sentiment score")
    colors = [
        "green" if value >= 0 else "red"
        for value in combined["sentiment"]
    ]
    sentiment_axis.bar(
        combined["date"],
        combined["sentiment"],
        color=colors,
        alpha=0.6,
    )

    figure.tight_layout()
    plt.title(f"{ticker.upper()} price vs. aggregated sentiment")
    plt.show()
