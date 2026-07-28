from typing import Iterator, Union
from http.client import HTTPResponse
from polygon import RESTClient
from polygon.rest.models import Agg
from datetime import datetime, timedelta
import pytz  # pip install pytz
from .loadToken import load_token


def calculate_ema(
    data: Union[Iterator[Agg], HTTPResponse],
    period: int = 20
) -> list[tuple[int, float]]:
    """
    Calculate the Exponential Moving Average (EMA) for a sequence of Agg objects.

    Args:
        data: An iterator (or HTTPResponse) yielding Agg instances, each of which
              has a .close (float) and .timestamp (int).
        period: The EMA lookback period (number of bars). Default is 20.

    Returns:
        A list of tuples (timestamp, ema_value). The first (period-1) bars
        don’t produce an EMA; the first EMA is the simple moving average of the
        first `period` closes, and subsequent EMAs follow the standard formula.
    """
    closes: list[float] = []
    timestamps: list[int] = []

    # 1) Pull out all closes and their timestamps
    for agg in data:
        closes.append(agg.close)
        timestamps.append(agg.timestamp)

    n = len(closes)
    if n < period:
        return []

    # 2) Initial SMA (first EMA) over the first 'period' closes
    initial_sma = sum(closes[0:period]) / period

    # 3) Store (timestamp, ema) pairs
    ema_values: list[tuple[int, float]] = []
    ema_values.append((timestamps[period - 1], initial_sma))

    # 4) Compute smoothing factor
    alpha = 2.0 / (period + 1)

    # 5) Now iterate from bar index 'period' → end, computing each subsequent EMA
    previous_ema = initial_sma
    for i in range(period, n):
        close_price = closes[i]
        ema_today = (close_price - previous_ema) * alpha + previous_ema
        ema_values.append((timestamps[i], ema_today))
        previous_ema = ema_today

    return ema_values


def format_ts(ts_ms: int) -> str:
    """
    Convert a Unix-ms timestamp (int) into a human-readable string (UTC).
    """
    return datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")


if __name__ == "__main__":
    # ——————————————————————————————————————————————————————————————————
    #  Replace "YOUR_POLYGON_API_KEY" below with your actual Polygon.io key.
    # ——————————————————————————————————————————————————————————————————
    client = RESTClient(load_token())
    ticker = "AAPL"

    # ----------------------------------------------
    # 1) Compute dynamic start/end dates in Eastern Time using pytz
    # ----------------------------------------------
    eastern_tz = pytz.timezone("US/Eastern")
    now_eastern = datetime.now(eastern_tz)       # current ET timestamp
    today_et = now_eastern.date()                 # e.g. 2025-06-04
    end_date = today_et.strftime("%Y-%m-%d")       # "2025-06-04"

    # Subtract ~400 calendar days to ensure ≥200 trading days of history
    lookback_days = 400
    start_date = (today_et - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    # e.g. if today_et = 2025-06-04, start_date → "2024-04-30"

    # ----------------------------------------------
    # 2) Fetch daily bars (including volume) from Polygon
    # ----------------------------------------------
    raw_aggs = client.list_aggs(
        ticker,
        1,               # 1-day bars
        "day",
        start_date,      # e.g. "2024-04-30"
        end_date,        # e.g. "2025-06-04"
        adjusted="true",
        sort="asc",
        limit=500        # up to 500 bars
    )

    # Convert the iterator into a list so we can use it multiple times
    stock_list = list(raw_aggs)

    # ----------------------------------------------
    # 3) Compute 50-day and 200-day EMAs, as before
    # ----------------------------------------------
    ema_50 = calculate_ema(stock_list, period=50)
    ema_200 = calculate_ema(stock_list, period=200)

    # ----------------------------------------------
    # 4) Extract volumes and timestamps into lists
    # ----------------------------------------------
    volumes = [agg.volume for agg in stock_list]
    timestamps = [agg.timestamp for agg in stock_list]

    # ----------------------------------------------
    # 5) Print results to the console
    # ----------------------------------------------
    print(f"Data fetched (ET) from {start_date} through {end_date}\n")

    # 5a) Print the EMA series
    print("=== 50-Day EMA Series ===")
    for ts, val in ema_50:
        print(f"{format_ts(ts)}  →  {val:.2f}")
    print()

    print("=== 200-Day EMA Series ===")
    for ts, val in ema_200:
        print(f"{format_ts(ts)}  →  {val:.2f}")
    print()

    # 5b) Print the most recent EMA values
    if ema_50:
        last_ts_50, last_val_50 = ema_50[-1]
        print(f"Most recent 50-day EMA as of {format_ts(last_ts_50)}: {last_val_50:.2f}")
    else:
        print("Not enough data to compute a 50-day EMA.")

    if ema_200:
        last_ts_200, last_val_200 = ema_200[-1]
        print(f"Most recent 200-day EMA as of {format_ts(last_ts_200)}: {last_val_200:.2f}")
    else:
        print("Not enough data to compute a 200-day EMA.")
    print()

    # 5c) Simple return of today's (most recent) volume
    if stock_list:
        last_agg = stock_list[-1]
        print(f"Today's ({format_ts(last_agg.timestamp)}) Volume: {last_agg.volume:,}")
    else:
        print("No bars returned by Polygon.")
    print()

    # 5d) Print every day's volume and indicate ↑ if it increased vs. prior day, ↓ if decreased
    print("=== Daily Volume and Change Indicator ===")
    for i in range(len(stock_list)):
        date_str = format_ts(timestamps[i])
        vol_today = volumes[i]

        if i == 0:
            # First day has no "previous" to compare
            print(f"{date_str}  →  Volume: {vol_today:,}  (N/A)")
        else:
            vol_prev = volumes[i - 1]
            if vol_today > vol_prev:
                pct = (vol_today - vol_prev) / vol_prev * 100.0
                print(f"{date_str}  →  Volume: {vol_today:,}  (↑{pct:.1f}%)")
            elif vol_today < vol_prev:
                pct = (vol_prev - vol_today) / vol_prev * 100.0
                print(f"{date_str}  →  Volume: {vol_today:,}  (↓{pct:.1f}%)")
            else:
                # volume is equal to previous day
                print(f"{date_str}  →  Volume: {vol_today:,}  (— 0.0%)")
    print()

    # 5e) Check if 20-day average volume has increased above the most recent 50-day EMA
    #     (Compute 20-day simple average volume, then compare to last 50-day EMA price.)
    if len(volumes) >= 20 and ema_50:
        avg_20_vol = sum(volumes[-20:]) / 20.0
        last_ema_50_price = ema_50[-1][1]  # price value
        if avg_20_vol > last_ema_50_price:
            print(
                f"20-Day Average Volume ({avg_20_vol:,.0f}) is above "
                f"the most recent 50-day EMA price ({last_ema_50_price:.2f})."
            )
        else:
            print(
                f"20-Day Average Volume ({avg_20_vol:,.0f}) is NOT above "
                f"the most recent 50-day EMA price ({last_ema_50_price:.2f})."
            )
    else:
        print("Not enough data to compare 20-day average volume with 50-day EMA.")
    print()

