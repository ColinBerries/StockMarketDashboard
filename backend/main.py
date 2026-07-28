import os
from dataclasses import asdict

from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS

from Signals import hurst, portfolio, tail_risk, vrp
from TechnicalAnalysis import callClosingPrices, calculateEma

app = Flask(__name__)
api = Api(app)
CORS(app)

DEFAULT_UNIVERSE = (
    'AAPL',
    'MSFT',
    'NVDA',
    'AMZN',
    'GOOGL',
    'META',
    'TSLA',
    'JPM',
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
            ticker_closes = {
                ticker: callClosingPrices.get_price_data(
                    ticker
                )['close'].tolist()
                for ticker in universe
            }

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

        return asdict(state)


api.add_resource(HelloWorld, '/tickers/<string:ticker>')
api.add_resource(EMA, '/ema/<string:ema>')
api.add_resource(TailRisk, '/signals/tail-risk/<string:ticker>')
api.add_resource(HurstSignal, '/signals/hurst/<string:ticker>')
api.add_resource(PortfolioLegs, '/portfolio/legs')

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=4999,
        threaded=True
    )
