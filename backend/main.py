import importlib.util
import os
from dataclasses import asdict
from pathlib import Path

from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS

from Signals import hurst, portfolio, tail_risk, vrp
from TechnicalAnalysis import (
    calculateAD,
    calculateEma,
    calculateMACD,
    calculateOBV,
    calculateRSI,
    callClosingPrices,
)

app = Flask(__name__)
api = Api(app)
CORS(app)

# "Sentiment Analysis" has a space in its directory name, which makes it an
# invalid Python package identifier -- load sentiment.py directly by file
# path instead of via a normal import statement.
_BACKEND_DIR = Path(__file__).resolve().parent
_sentiment_path = _BACKEND_DIR / "Sentiment Analysis" / "sentiment.py"
_sentiment_spec = importlib.util.spec_from_file_location(
    "sentiment_module", _sentiment_path
)
sentiment_module = importlib.util.module_from_spec(_sentiment_spec)
_sentiment_spec.loader.exec_module(sentiment_module)

_DASHBOARD_HISTORY_POINTS = 180  # trailing days of history returned per series

DEFAULT_UNIVERSE = (
    # Tech
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD', 'NFLX', 'CRM',
    # Financials
    'JPM', 'BAC', 'GS', 'V', 'MA',
    # Healthcare
    'UNH', 'JNJ', 'PFE', 'LLY',
    # Consumer
    'WMT', 'COST', 'HD', 'DIS', 'KO', 'PEP', 'MCD',
    # Energy / industrials
    'XOM', 'CVX', 'CAT', 'BA',
)


def _configured_universe() -> list[str]:
    configured = os.getenv('PORTFOLIO_TICKERS', '')
    raw_tickers = configured.split(',') if configured else DEFAULT_UNIVERSE
    return list(dict.fromkeys(
        ticker.strip().upper()
        for ticker in raw_tickers
        if ticker.strip()
    ))


def _latest_hurst(closes: list[float], window: int = 32) -> float | None:
    values = hurst.moving_hurst(closes, window)
    return values[-1] if values else None


def _market_tail_percentile(
    closes: list[float],
    k: int = 30,
    window: int = 252,
) -> float:
    if len(closes) <= k:
        raise ValueError(f'Need at least {k + 1} closes for market tail risk')

    effective_window = min(window, len(closes))
    endpoints = list(range(effective_window, len(closes) + 1, 5))
    if not endpoints or endpoints[-1] != len(closes):
        endpoints.append(len(closes))

    observations = []
    for endpoint in endpoints:
        segment = closes[endpoint - effective_window:endpoint]
        try:
            observations.append(tail_risk.market_tail_risk(segment, k))
        except ValueError:
            continue

    if not observations:
        raise ValueError('Unable to calculate market tail-risk history')
    current = observations[-1]
    return 100.0 * sum(
        observation <= current for observation in observations
    ) / len(observations)


def _configured_vrp(index_closes: list[float]) -> tuple[float, list[float]]:
    implied_vol = os.getenv('IMPLIED_VOL_1M')
    if not implied_vol:
        return 0.0, []

    current = vrp.vrp(float(implied_vol), index_closes)
    raw_history = os.getenv('VRP_HISTORY', '')
    history = [
        float(value.strip())
        for value in raw_history.split(',')
        if value.strip()
    ]
    return current, history


class HelloWorld(Resource):
    def get(self, ticker: str):
        new_ticker = ticker.upper()
        closing_prices = callClosingPrices.get_price_data(new_ticker)


        return {
            'ticker': new_ticker,
            'closingPrices': closing_prices.to_dict(orient='records'),
        }

class EMA(Resource):
    def get(self, ema: str):
        new_ema = ema.upper()
        period = request.args.get('period', default=50, type=int)

        if period is None or period < 1:
            return {'ticker': new_ema, 'error': 'period must be a positive integer'}, 400

        price_df = callClosingPrices.get_price_data(new_ema)
        closes = price_df['close'].tolist()

        if len(closes) < period:
            return {
                'ticker': new_ema,
                'error': f'Not enough data points ({len(closes)}) for period {period}',
            }, 400

        ema_series = calculateEma.get_ema_list(closes, period)
        aligned_dates = price_df.index[period - 1:]

        ema_records = [
            {'date': str(date), 'ema': value}
            for date, value in zip(aligned_dates, ema_series)
        ]

        return {
            'ticker': new_ema,
            'period': period,
            'emaValue': ema_records,
        }


class TailRisk(Resource):
    def get(self, ticker: str):
        symbol = ticker.upper()
        k = request.args.get(
            'k',
            default=30 if symbol == 'SPY' else 20,
            type=int,
        )
        if k is None or k < 2:
            return {'ticker': symbol, 'error': 'k must be at least 2'}, 400

        try:
            closes = callClosingPrices.get_price_data(symbol)['close'].tolist()
            if symbol == 'SPY':
                risk_value = tail_risk.market_tail_risk(closes, k)
            else:
                risks = tail_risk.firm_tail_risk({symbol: closes}, k)
                if symbol not in risks:
                    raise ValueError(
                        f'Need at least {k + 2} closes for tail risk'
                    )
                risk_value = risks[symbol]
        except ValueError as error:
            return {'ticker': symbol, 'error': str(error)}, 400
        except Exception as error:
            return {'ticker': symbol, 'error': str(error)}, 502

        return {
            'ticker': symbol,
            'k': k,
            'tailRisk': risk_value,
            'tailIndex': 1.0 / risk_value,
        }


class HurstSignal(Resource):
    def get(self, ticker: str):
        symbol = ticker.upper()
        window = request.args.get('window', default=32, type=int)
        if window is None or window < 9:
            return {
                'ticker': symbol,
                'error': 'window must contain at least 9 prices',
            }, 400

        try:
            closes = callClosingPrices.get_price_data(symbol)['close'].tolist()
            value = _latest_hurst(closes, window)
        except ValueError as error:
            return {'ticker': symbol, 'error': str(error)}, 400
        except Exception as error:
            return {'ticker': symbol, 'error': str(error)}, 502

        if value is None:
            return {
                'ticker': symbol,
                'error': f'Not enough data for a {window}-day Hurst window',
            }, 400
        return {
            'ticker': symbol,
            'window': window,
            'hurst': value,
            'regime': hurst.hurst_regime(value),
        }


class PortfolioLegs(Resource):
    def get(self):
        try:
            index_closes = callClosingPrices.get_price_data(
                'SPY'
            )['close'].tolist()
            universe = _configured_universe()

            ticker_closes = {}
            failed_tickers: dict[str, str] = {}
            for ticker in universe:
                try:
                    ticker_closes[ticker] = callClosingPrices.get_price_data(
                        ticker
                    )['close'].tolist()
                except Exception as error:
                    # Skip this ticker rather than failing the whole
                    # portfolio view -- one rate-limited or delisted
                    # ticker shouldn't blank out every other signal.
                    failed_tickers[ticker] = str(error)

            if not ticker_closes:
                raise ValueError(
                    'Unable to fetch price data for any ticker in the '
                    'configured universe.'
                )

            lambda_percentile = _market_tail_percentile(index_closes)
            firm_ranks = tail_risk.firm_tail_risk(ticker_closes)
            hurst_values = {
                ticker: _latest_hurst(closes)
                for ticker, closes in ticker_closes.items()
            }
            vrp_value, vrp_history = _configured_vrp(index_closes)
            state = portfolio.build_portfolio_state(
                lambda_t_percentile=lambda_percentile,
                firm_tail_ranks=firm_ranks,
                hurst_by_ticker=hurst_values,
                vrp_value=vrp_value,
                vrp_history=vrp_history,
            )
        except ValueError as error:
            return {'error': str(error)}, 400
        except Exception as error:
            return {'error': str(error)}, 502

        payload = asdict(state)
        payload['universe'] = universe
        if failed_tickers:
            payload['universeErrors'] = failed_tickers
        return payload


def _safe_section(compute, results: dict, errors: dict, key: str) -> None:
    """Run one indicator calc; record its own error without failing the rest."""
    try:
        results[key] = compute()
    except Exception as error:  # noqa: BLE001 - intentionally broad, per-section
        results[key] = None
        errors[key] = str(error)


class TickerDashboard(Resource):
    """
    Combined read-out for a single ticker: price history, EMA 20/50, RSI,
    MACD, OBV, Accumulation/Distribution, volume, sentiment, and tail risk,
    in one response so the frontend can render a full dashboard from a
    single request. Each section fails independently -- a missing
    NEWS_API_KEY, for example, only blanks out the sentiment field.
    """

    def get(self, ticker: str):
        symbol = ticker.upper().strip()
        if not symbol:
            return {'error': 'ticker cannot be empty'}, 400

        try:
            price_df = callClosingPrices.get_price_data(symbol)
        except Exception as error:
            return {'ticker': symbol, 'error': str(error)}, 502

        closes = price_df['close'].tolist()
        highs = price_df['high'].tolist()
        lows = price_df['low'].tolist()
        volumes = price_df['volume'].tolist()
        dates = [str(ts.date()) for ts in price_df.index]

        n = _DASHBOARD_HISTORY_POINTS
        results: dict = {
            'ticker': symbol,
            'dates': dates[-n:],
            'closes': closes[-n:],
        }
        errors: dict = {}

        _safe_section(
            lambda: calculateEma.get_ema_list(closes, 20)[-n:],
            results, errors, 'ema20',
        )
        _safe_section(
            lambda: calculateEma.get_ema_list(closes, 50)[-n:],
            results, errors, 'ema50',
        )
        _safe_section(
            lambda: calculateRSI.calculate_rsi(closes, 14)[-n:],
            results, errors, 'rsi',
        )

        def _macd():
            macd_df = calculateMACD.calculate_macd(price_df)
            return {
                'macd': macd_df['MACD'].tolist()[-n:],
                'signal': macd_df['Signal'].tolist()[-n:],
                'histogram': macd_df['Histogram'].tolist()[-n:],
            }
        _safe_section(_macd, results, errors, 'macd')

        _safe_section(
            lambda: calculateOBV.compute_obv(closes, volumes)[-n:],
            results, errors, 'obv',
        )
        _safe_section(
            lambda: calculateAD.calculate_ad(closes, highs, lows, volumes)[-n:],
            results, errors, 'ad',
        )
        _safe_section(lambda: volumes[-n:], results, errors, 'volume')
        _safe_section(
            lambda: sentiment_module.average_sentiment(symbol),
            results, errors, 'sentiment',
        )
        _safe_section(
            lambda: tail_risk.firm_tail_risk({symbol: closes}, 20).get(symbol),
            results, errors, 'tailRisk',
        )

        def _hurst_section():
            value = _latest_hurst(closes)
            return {'value': value, 'regime': hurst.hurst_regime(value)}
        _safe_section(_hurst_section, results, errors, 'hurst')

        if errors:
            results['errors'] = errors
        return results


api.add_resource(HelloWorld, '/tickers/<string:ticker>')
api.add_resource(EMA, '/ema/<string:ema>')
api.add_resource(TailRisk, '/signals/tail-risk/<string:ticker>')
api.add_resource(HurstSignal, '/signals/hurst/<string:ticker>')
api.add_resource(PortfolioLegs, '/portfolio/legs')
api.add_resource(TickerDashboard, '/dashboard/<string:ticker>')

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=4999,
        threaded=True
    )
