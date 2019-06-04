#!/usr/bin/env python
# encoding: utf-8
import ccxt
import sys
from time import time_ns, ctime
from random import randint, seed

from yat.calcus import rounded_to_precision
from payload.orderbook import Orderbook


class RestClient:

    def __init__(self, window: int = 100, api_key: str = None, secret: str = None,
                 verbose: bool = False, logger: object = None, marketonly: bool = False):
        '''
        Exchange initialising
        '''
        self.logger = logger
        self.dry_run = False
        self.exchange_name = 'binance'
        self.marketonly = marketonly
        self._secret = secret
        self._api_key = api_key
        self.exchange: ccxt.binance = ccxt.binance({"apiKey": self._api_key,
                                      "secret": self._secret,
                                      'verbose': verbose,
                                      'options': {'adjustForTimeDifference': True,
                                                  'defaultTimeInForce': 'GTC', },  # 'GTC', 'IOC'
                                      'enableRateLimit': True})
        self.exchange_name = self.exchange.describe()['id']
        # Initialize the Orderbook with a set of empty dicts and other defaults
        self.orderbook = Orderbook(window, logger)
        # Load markets on initialization
        self.markets = self.exchange.load_markets()
        # Sort only active markets
        self.markets = {x: y for x, y in self.markets.items() if y['active']}
        self.all_tickers: dict = None
        # Order and trade sets
        self.confirm_trade_collector = list()
        self._order_index = 0
        self._ex_index = 0
        self.order_history = dict()
        self._candlesticks = dict()
        self._trades = dict()
        self.balances = list()

    # region Order

    def place_multiple_orders(self, quotes: list):
        """
        Feed with quotes
        :param quotes:
        :return:
        """
        if not isinstance(quotes, list):
            return False
        if len(quotes) < 1:
            return False
        for q in quotes:
            response = self.create_order(**q)
            if isinstance(response, dict):
                if 'id' in response:
                    self.order_history[response['id']] = response
                else:
                    self.order_history[response['client_order_id']] = response
                    self.order_history[response['client_order_id']]['id'] = response['client_order_id']

    def create_order(self, symbol: str, side: str, order_type: str, amount,
                     price=None, client_order_id=None):
        """ Submit a new order
        :param symbol: the market symbol (ie: BTC/USDT)
        :param side: "BUY" or "SELL"
        :param order_type: "LIMIT" or "MARKET"
        :param amount: the amount to buy/sell
        :param price: the price to buy/sell at, used in LIMIT order type
        :param client_order_id: A unique id for the order. Automatically generated if not sent (optional)
        :param timeInForce: 'GTC' = Good Till Cancel(default), 'IOC' = Immediate Or Cancel
        :param stop_price: Used with stop orders (optional)
        :param iceberg_qty: Used with iceberg orders (optional)
        :return: response from an exchange with order data {'id': '416850076', 'timestamp': 1559577269494,
        'datetime': '2019-06-03T15:54:29.494Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USDT','type': 'limit',
        'side': 'sell', 'price': 100.0, 'amount': 0.001, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining':
        0.001, 'status': 'open', 'fee': None, 'trades': None}
        :rtype: dict
        """
        # Create random number
        if client_order_id is None:
            seed(time_ns())
            client_order_id = '654'.join(["%s" % randint(0, 9) for _ in range(0, 8)])
        else:
            client_order_id = client_order_id
        # Check market filters before quoting
        if amount and price:
            cost = float(amount) * float(price)
            if self.markets[symbol]['limits']['cost']['min'] > cost:
                # TODO return order_dict instead
                return False
        if self.marketonly:
            order_type = 'MARKET'
        # Build order dict, use test extra param for testing
        if self.dry_run:
            order_dict = dict(symbol=symbol, type=order_type,
                              side=side, amount=amount, price=price,
                              params=dict(test=True))
        else:
            order_dict = dict(symbol=symbol, type=order_type,
                              side=side, amount=amount, price=price)
        try:
            order_c = self.exchange.create_order(**order_dict)
            order_c['client_order_id'] = client_order_id
            return order_c
        except Exception as e:
            order_dict['status'] = type(e).__name__
            order_dict['timestamp'] = time_ns()
            order_dict['client_order_id'] = client_order_id
            return order_dict

    def cancel_order(self, orderId=None, symbol=None):
        """
        Cancel order by symbol and order id
        :param orderId:
        :param symbol:
        :return:
        """
        if symbol and orderId is not None:
            order_dict = dict(orderId=orderId, symbol=symbol, params={})
            try:
                response = self.exchange.cancel_order(**order_dict)
                return response
            except Exception as e:
                order_dict['status'] = type(e).__name__
                order_dict['timestamp'] = time_ns()
                return order_dict
        else:
            return False

    def fetch_processed_orders(self):
        if len(self.order_history) == 0:
            return False
        for x, y in self.order_history.items():
            try:
                resp = self.exchange.fetch_order(y['id'], y['symbol'])
                self.order_history[x] = resp
            except Exception as e:
                self.order_history[x]['status'] = type(e).__name__

    def cancel_processed_orders(self):
        if len(self.order_history) == 0:
            return False
        for x, y in self.order_history.items():
            if y['status'] == 'open':
                try:
                    resp = self.exchange.fetch_order(y['id'], y['symbol'])
                    self.order_history[x] = resp
                except Exception as e:
                    self.order_history[x]['status'] = type(e).__name__

    # endregion

    # region Balance

    @staticmethod
    def _filter_not_null(balances):
        filtered_balances = {}
        for x in balances['info']['balances']:
            if (float(x['free']) > 0) or (float(x['locked']) > 0):
                filtered_balances[x['asset']] = {'free': x['free'],
                                                 'locked': x['locked'],
                                                 'all': float(x['free']) + float(x['locked'])}
        return filtered_balances

    def fetch_balances(self):
        """
        Fetch and filter not null balances
        """
        try:
            result = self.exchange.fetch_balance()
            self.balances = self._filter_not_null(result)
        except Exception as e:
            # print(type(e).__name__, e.args, str(e))
            self.logger.error('While fetching tickers next error occur: ', type(e).__name__, "!!!", e.args)
            self.logger.error("Exiting")
            self.balances.clear()
            # sys.exit()

    # endregion

    # region Orderbook

    def fetch_ob(self, symbol: str, run_step: int, spread_lag_size: int = -20, limit: int = 20) -> None:
        """
        Fetch orderbook of symbol with fixed limit and call update_ob

        :param symbol: symbol which orderbook to fetch
        :param run_step: step number
        :param spread_lag_size: lag_size param for spread counting in _update_tob
        :param limit: order book depth
        :return:
        """
        try:
            resp = self.exchange.fetch_order_book(symbol, limit=limit)
            self.orderbook.update_ob(resp, run_step, spread_lag_size)
            # self.update_ob(resp, run_step, spread_lag_size)
        except Exception as e:
            self.logger.exception('While fetching orderbook next error occur:', exc_info=True)
            # print(type(e).__name__, e.args, str(e))
            # print('While fetching orderbook next error occur: ', type(e).__name__, "-", str(e))
            # print("Exiting")
            sys.exit(56)

    # endregion

    # region OHLCV Candles

    def get_ohlcv(self, symbol, timeframe='1m', limit=500):
        '''
        Fetch exchanges ticker for necessary pair
        :param symbol: Symbol (i.e. BNB/BTC)
        :param timeframe: 1m, 5m...
        :additional param since: by default return since now
        :addition param limit: default == max == 500
        :return: ccxt ohlcv
        '''
        try:
            response = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.logger.error("Exiting")
            sys.exit()
        return response

    # endregion

    # region Ticker

    def calc_tickers(self, tickers: list = None):
        """
        Check for tickers list or iterate throw all tickers to add spread, mid_price data.
        Add data to self.all_tickers container
        :param tickers: list of valid tickers
        :return:
        """
        if tickers is not None:
            m = tickers
        else:
            m = self.all_tickers.keys()
        for s in m:
            tob_ask = self.all_tickers[s]['ask']
            tob_bid = self.all_tickers[s]['bid']
            # Calculate some digits
            mid_price = rounded_to_precision((tob_bid + tob_ask) / 2, 8)
            spread = rounded_to_precision((tob_ask - tob_bid), 8)
            if mid_price > 0:
                spread_p = rounded_to_precision(100 * spread / mid_price, 4)
            else:
                spread_p = 0
            # Update all_tickers with new data
            self.all_tickers[s]['mid_price'] = mid_price
            self.all_tickers[s]['spread'] = spread
            self.all_tickers[s]['spread_p'] = spread_p
            self.all_tickers[s]['timestamp'] = time_ns()

    def clear_empty_tickers(self):
        """
        Check for non empty tickers and clear tickers without any quotes
        Building new dict with non zero quote prices
        """
        if self.all_tickers is not None:
            self.all_tickers = {x: y for x, y in self.all_tickers.items() if y['bid'] > 0 and y['ask'] > 0}

    def process_tickers(self, tickers: list = None):
        """
        Call http api for all tickers data.
        Delete empty responses from all_tickers dict.
        Calculate inplace data for tickers and add timestamp of calculation.
        :param tickers: pass tickers list to process only that tickers
        :type tickers: list
        """
        self.get_all_tickers()
        self.clear_empty_tickers()
        self.calc_tickers(tickers)

    def get_all_tickers(self):
        """
        Blocking method!
        Fetch exchanges tickers for all pairs
        Save response to all_tickers, clear previous state
        """
        try:
            response = self.exchange.fetch_bids_asks()
            if self.all_tickers is not None:
                self.all_tickers.clear()
            self.all_tickers = response
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.all_tickers = None
            # self.logger.error("Exiting")
            # sys.exit()

    def _fetch_ticker(self, symbol):
        """
        Fetch symbol ticker
        :param symbol:
        :return:
        """
        try:
            response = self.exchange.fetch_ticker(symbol)
            self.all_tickers[symbol] = response
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.logger.error("Exiting")
            sys.exit()

    # endregion
