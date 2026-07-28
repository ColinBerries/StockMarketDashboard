"""
Local diagnostic dashboard that imports the backend calculations directly.

This is separate from main.py's production API. It displays EMA, RSI, MACD,
OBV, Accumulation/Distribution, volume, sentiment, tail risk, Hurst, and the
composed portfolio legs without requiring the React frontend.

Run from backend/ with ``python dev_dashboard.py``, then open
http://localhost:5050. POLYGON_TOKEN is required for uncached prices;
NEWS_API_KEY is optional and only affects the sentiment badge.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from TechnicalAnalysis import (  # noqa: E402
    calculateAD,
    calculateEma,
    calculateMACD,
    calculateOBV,
    calculateRSI,
    callClosingPrices,
)
from Signals import hurst as hurst_signal  # noqa: E402
from Signals import tail_risk  # noqa: E402

# Importing main is safe because its server starts only under __main__. Reusing
# its helpers keeps portfolio behavior identical to the production endpoint.
import main as backend_main  # noqa: E402


_sentiment_path = BACKEND_DIR / "Sentiment Analysis" / "sentiment.py"
_sentiment_spec = importlib.util.spec_from_file_location(
    "dev_sentiment",
    _sentiment_path,
)
if _sentiment_spec is None or _sentiment_spec.loader is None:
    raise ImportError(f"Could not load sentiment module from {_sentiment_path}")
sentiment_module = importlib.util.module_from_spec(_sentiment_spec)
_sentiment_spec.loader.exec_module(sentiment_module)

app = Flask(__name__)
CORS(app)

_STATIC_DIR = BACKEND_DIR / "dev_dashboard_static"
_HISTORY_POINTS = 180


def _safe(
    section_name: str,
    calculation: Callable[[], Any],
    results: dict[str, Any],
    errors: dict[str, str],
) -> None:
    """Run one indicator without allowing its failure to hide other results."""
    try:
        results[section_name] = calculation()
    except Exception as error:  # Intentionally isolates each diagnostic panel.
        results[section_name] = None
        errors[section_name] = str(error)


@app.route("/")
def index():
    return send_from_directory(_STATIC_DIR, "index.html")


@app.route("/api/dashboard/<ticker>")
def dashboard_data(ticker: str):
    symbol = ticker.upper().strip()
    if not symbol:
        return jsonify({"error": "ticker cannot be empty"}), 400

    try:
        price_frame = callClosingPrices.get_price_data(symbol)
        closes = price_frame["close"].tolist()
        highs = price_frame["high"].tolist()
        lows = price_frame["low"].tolist()
        volumes = price_frame["volume"].tolist()
        dates = [str(timestamp.date()) for timestamp in price_frame.index]
    except Exception as error:
        return jsonify({"ticker": symbol, "error": str(error)}), 502

    results: dict[str, Any] = {
        "ticker": symbol,
        "dates": dates[-_HISTORY_POINTS:],
        "closes": closes[-_HISTORY_POINTS:],
    }
    errors: dict[str, str] = {}

    _safe(
        "ema20",
        lambda: calculateEma.get_ema_list(closes, 20)[-_HISTORY_POINTS:],
        results,
        errors,
    )
    _safe(
        "ema50",
        lambda: calculateEma.get_ema_list(closes, 50)[-_HISTORY_POINTS:],
        results,
        errors,
    )
    _safe(
        "rsi",
        lambda: calculateRSI.calculate_rsi(closes, 14)[-_HISTORY_POINTS:],
        results,
        errors,
    )

    def calculate_macd() -> dict[str, list[float]]:
        macd_frame = calculateMACD.calculate_macd(price_frame)
        return {
            "macd": macd_frame["MACD"].tolist()[-_HISTORY_POINTS:],
            "signal": macd_frame["Signal"].tolist()[-_HISTORY_POINTS:],
            "histogram": macd_frame["Histogram"].tolist()[-_HISTORY_POINTS:],
        }

    _safe("macd", calculate_macd, results, errors)
    _safe(
        "obv",
        lambda: calculateOBV.compute_obv(
            closes,
            volumes,
        )[-_HISTORY_POINTS:],
        results,
        errors,
    )
    _safe(
        "ad",
        lambda: calculateAD.calculate_ad(
            closes,
            highs,
            lows,
            volumes,
        )[-_HISTORY_POINTS:],
        results,
        errors,
    )
    _safe(
        "volume",
        lambda: volumes[-_HISTORY_POINTS:],
        results,
        errors,
    )
    _safe(
        "sentiment",
        lambda: sentiment_module.average_sentiment(symbol),
        results,
        errors,
    )
    _safe(
        "tailRisk",
        lambda: tail_risk.firm_tail_risk({symbol: closes}, 20).get(symbol),
        results,
        errors,
    )

    def calculate_hurst() -> dict[str, float | str | None]:
        value = backend_main._latest_hurst(closes)
        return {
            "value": value,
            "regime": hurst_signal.hurst_regime(value),
        }

    _safe("hurst", calculate_hurst, results, errors)

    if errors:
        results["errors"] = errors
    return jsonify(results)


@app.route("/api/portfolio")
def portfolio_data():
    payload = backend_main.PortfolioLegs().get()
    if isinstance(payload, tuple):
        body, status = payload
        return jsonify(body), status
    return jsonify(payload)


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5050,
        threaded=True,
    )
