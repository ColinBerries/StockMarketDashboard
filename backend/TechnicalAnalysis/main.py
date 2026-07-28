from polygon import RESTClient

from .calculateEma import calculate_ema
from .loadToken import load_token


if __name__ == "__main__":
    ticker = "AAPL"
    client = RESTClient(load_token())
    stock_data = list(
        client.list_aggs(
            ticker,
            1,
            "day",
            "2024-01-01",
            "2025-05-05",
            adjusted="true",
            sort="asc",
            limit=120,
        )
    )
    print(calculate_ema([bar.close for bar in stock_data]))
