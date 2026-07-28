from polygon import RESTClient
from polygon.rest.models import Agg
from datetime import datetime, timedelta, timezone
import pytz
from .loadToken import load_token

def fetch_daily_bars(ticker: str, lookback_days: int = 365) -> list[Agg]:
    """Fetch daily bars for the past lookback_days in Eastern Time."""
    eastern = pytz.timezone("US/Eastern")
    today_et = datetime.now(eastern).date()
    start = (today_et - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end   = today_et.strftime("%Y-%m-%d")

    client = RESTClient(load_token())
    raw = client.list_aggs(
        ticker, 1, "day", start, end,
        adjusted="true", sort="asc", limit=lookback_days + 5
    )
    return list(raw)

def calculate_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """
    Compute the Wilder RSI for a list of closing prices.
    Returns a list of RSI values, with None for indices < period.
    """
    if len(closes) < period + 1:
        return [None] * len(closes)

    gains = [0.0]
    losses = [0.0]
    # 1) Compute daily gains/losses
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i-1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    # 2) Initial average gain/loss
    avg_gain = sum(gains[1:period+1]) / period
    avg_loss = sum(losses[1:period+1]) / period

    rsi = [None] * (period)
    # 3) First RSI value
    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
    rsi.append(100 - (100 / (1 + rs)))

    # 4) Wilder's smoothing
    for i in range(period+1, len(closes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
        rsi.append(100 - (100 / (1 + rs)))

    return rsi

def calculate_sma(values: list[float | None], period: int) -> list[float | None]:
    """
    Simple Moving Average that handles None values: only returns a number
    when the full period of non-None values is available.
    """
    sma = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i+1-period:i+1]
        if None not in window:
            sma[i] = sum(window) / period
    return sma

if __name__ == "__main__":
    ticker = "AAPL"
    bars   = fetch_daily_bars(ticker, lookback_days=365)

    # Extract closing prices and timestamps
    closes     = [bar.close     for bar in bars]
    timestamps = [bar.timestamp for bar in bars]

    # Calculate 14-period RSI
    period_rsi = 14
    rsi_values = calculate_rsi(closes, period=period_rsi)

    # Calculate a 9-period SMA of the RSI (RSI-MA)
    period_ma  = 9
    rsi_ma     = calculate_sma(rsi_values, period_ma)

    # Print results
    print(f"{'Date':<12} {'Close':>8} {'RSI':>6} {'RSI_MA':>8}")
    print("-" * 36)
    for ts, close, rsi, ma in zip(timestamps, closes, rsi_values, rsi_ma):
        date_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        rsi_str  = f"{rsi:6.2f}" if rsi is not None else "   nan"
        ma_str   = f"{ma:8.2f}" if ma is not None else "     nan"
        print(f"{date_str:<12} {close:8.2f} {rsi_str} {ma_str}")
