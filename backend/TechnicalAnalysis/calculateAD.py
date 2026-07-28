from datetime import datetime, timedelta, timezone

import pytz
from polygon import RESTClient

from .loadToken import load_token


def calculate_ad(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    volumes: list[float],
) -> list[float]:
    """
    Accumulation/Distribution line.
    MFM = ((close - low) - (high - close)) / (high - low)
    MFV = MFM * volume
    AD  = cumulative sum of MFV
    """
    lengths = {len(closes), len(highs), len(lows), len(volumes)}
    if len(lengths) != 1:
        raise ValueError("closes, highs, lows, and volumes must have equal lengths")

    ad = [0.0] * len(closes)
    running_total = 0.0
    for i in range(len(closes)):
        high_low_range = highs[i] - lows[i]
        if high_low_range == 0:
            mfm = 0.0
        else:
            mfm = (
                (closes[i] - lows[i]) - (highs[i] - closes[i])
            ) / high_low_range
        mfv = mfm * volumes[i]
        running_total += mfv
        ad[i] = running_total
    return ad


if __name__ == "__main__":
    ticker = "AAPL"
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()
    start = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    client = RESTClient(load_token())
    bars = list(
        client.list_aggs(
            ticker,
            1,
            "day",
            start,
            end,
            adjusted="true",
            sort="asc",
            limit=500,
        )
    )
    ad_values = calculate_ad(
        [bar.close for bar in bars],
        [bar.high for bar in bars],
        [bar.low for bar in bars],
        [bar.volume for bar in bars],
    )

    print(f"{'Date':<12} {'AD':>16}")
    print("-" * 29)
    for bar, value in zip(bars, ad_values):
        date = datetime.fromtimestamp(
            bar.timestamp / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        print(f"{date:<12} {value:>16.2f}")
