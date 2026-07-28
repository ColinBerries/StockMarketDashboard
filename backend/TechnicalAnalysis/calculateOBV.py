from datetime import datetime, timedelta
from typing import Union

import pytz
import statistics
from polygon import RESTClient

from .loadToken import load_token


def format_ts(ts_ms: int) -> str:
    return datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")


def fetch_bars(ticker: str, lookback_days: int = 400):
    eastern = pytz.timezone("US/Eastern")
    today_et = datetime.now(eastern).date()
    start = (today_et - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = today_et.strftime("%Y-%m-%d")

    client = RESTClient(load_token())
    raw = client.list_aggs(
        ticker,
        1,
        "day",
        start,
        end,
        adjusted="true",
        sort="asc",
        limit=500,
    )
    return list(raw)


def compute_obv(closes: list[float], volumes: list[int]) -> list[float]:
    obv = [0.0] * len(closes)
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]
    return obv


def ema_list(values: list[float], period: int) -> list[Union[float, None]]:
    if len(values) < period:
        return [None] * len(values)
    alpha = 2.0 / (period + 1)
    ema = [None] * (period - 1)
    sma = sum(values[:period]) / period
    ema.append(sma)
    for value in values[period:]:
        sma = (value - ema[-1]) * alpha + ema[-1]
        ema.append(sma)
    return ema


if __name__ == "__main__":
    ticker = "AAPL"
    bars = fetch_bars(ticker)

    closes = [bar.close for bar in bars]
    volumes = [bar.volume for bar in bars]
    timestamps = [bar.timestamp for bar in bars]

    obv = compute_obv(closes, volumes)

    ema_period = 20
    obv_ema = ema_list(obv, ema_period)

    bb_k = 2.0
    bb_upper = [None] * len(obv)
    bb_lower = [None] * len(obv)
    for i in range(len(obv)):
        if i >= ema_period - 1 and obv_ema[i] is not None:
            window = obv[i + 1 - ema_period : i + 1]
            sd = statistics.pstdev(window)
            bb_upper[i] = obv_ema[i] + bb_k * sd
            bb_lower[i] = obv_ema[i] - bb_k * sd

    squeeze_lookback = 6
    signals = []
    print("Date       |    OBV    |  OBV_EMA  |   BB_UP   |  BB_LOW   | Signal")
    print("-" * 70)
    for i in range(len(obv)):
        date = format_ts(timestamps[i])
        value = obv[i]
        moving_average = (
            obv_ema[i] if obv_ema[i] is not None else float("nan")
        )
        upper = bb_upper[i] if bb_upper[i] is not None else float("nan")
        lower = bb_lower[i] if bb_lower[i] is not None else float("nan")

        flag = ""
        if bb_upper[i] is not None and value > bb_upper[i]:
            flag = "Overbought"
        elif bb_lower[i] is not None and value < bb_lower[i]:
            flag = "Oversold"
        if (
            bb_upper[i] is not None
            and bb_lower[i] is not None
            and i >= squeeze_lookback - 1
        ):
            widths = [
                bb_upper[j] - bb_lower[j]
                for j in range(i + 1 - squeeze_lookback, i + 1)
                if bb_upper[j] is not None and bb_lower[j] is not None
            ]
            if widths and widths[-1] == min(widths):
                flag = f"{flag} & Squeeze" if flag else "Squeeze"

        print(
            f"{date}  | {value:10.0f} | {moving_average:9.2f} | "
            f"{upper:9.2f} | {lower:9.2f} | {flag or '--'}"
        )
        if flag:
            signals.append((i, flag))

    lookahead = 3
    print("\nPrice movement after signals:")
    for idx, flag in signals:
        if idx + lookahead < len(closes):
            start_price = closes[idx]
            future_price = closes[idx + lookahead]
            delta = future_price - start_price
            direction = "up" if delta > 0 else ("down" if delta < 0 else "flat")
            print(
                f"{format_ts(timestamps[idx])} ({flag}): "
                f"price moved {direction} from {start_price:.2f} to "
                f"{future_price:.2f} in {lookahead} days"
            )
        else:
            print(
                f"{format_ts(timestamps[idx])} ({flag}): "
                f"not enough future data for {lookahead}-day lookahead"
            )
