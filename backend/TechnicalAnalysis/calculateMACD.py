import pandas as pd

from .callClosingPrices import get_price_data
from .loadToken import load_token


def fetch_last_year_data(symbol: str) -> pd.DataFrame:
    """Return approximately one trading year of Polygon daily bars."""
    return get_price_data(symbol).tail(252).copy()


def calculate_macd(
    data: pd.DataFrame,
    short_span: int = 12,
    long_span: int = 26,
    signal_span: int = 9,
) -> pd.DataFrame:
    """
    Add MACD, signal, and histogram columns to Polygon price data.

    ``data`` must use the lowercase ``close`` column returned by
    ``callClosingPrices.get_price_data``.
    """
    if "close" not in data:
        raise ValueError("Expected a DataFrame with a lowercase 'close' column")

    frame = data.copy()
    short_ema = frame["close"].ewm(span=short_span, adjust=False).mean()
    long_ema = frame["close"].ewm(span=long_span, adjust=False).mean()
    frame["MACD"] = short_ema - long_ema
    frame["Signal"] = frame["MACD"].ewm(span=signal_span, adjust=False).mean()
    frame["Histogram"] = frame["MACD"] - frame["Signal"]
    return frame


def _test_calculate_macd() -> None:
    dates = pd.date_range("2020-01-01", periods=50)
    data = pd.DataFrame({"close": range(50)}, index=dates)
    result = calculate_macd(data)
    expected = ["MACD", "Signal", "Histogram"]
    assert all(column in result.columns for column in expected)
    assert not result[expected].isna().any().any()


if __name__ == "__main__":
    _test_calculate_macd()

    symbol = input("Enter ticker symbol (e.g., AAPL): ").upper().strip()
    if not load_token():
        print("No POLYGON_TOKEN set; using cached data if available.")
    data = fetch_last_year_data(symbol)
    if data.empty:
        print(f"No data found for {symbol}.")
    else:
        macd = calculate_macd(data)
        macd_value = macd["MACD"].iloc[-1]
        signal_value = macd["Signal"].iloc[-1]
        histogram = macd["Histogram"].iloc[-1]
        print(f"\nLatest MACD values for {symbol}:")
        print(f"MACD: {macd_value:.6f}")
        print(f"Signal: {signal_value:.6f}")
        print(f"Histogram: {histogram:.6f}")
