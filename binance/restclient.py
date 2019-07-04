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
        self.possible_timeframes = {
            '1m':  '1m',
            '3m':  '3m',
            '5m':  '5m',
            '15m': '15m',
            '30m': '30m',
            '1h':  '1h',
            '2h':  '2h',
            '4h':  '4h',
            '6h':  '6h',
            '8h':  '8h',
            '12h': '12h',
            '1d':  '1d',
            '3d':  '3d',
            '1w':  '1w', }
        # Initialize the Orderbook with a set of empty dicts and other defaults
        self.orderbook = Orderbook(window, logger)
        # Load markets on initialization
        try:
            self.markets = self.exchange.load_markets()
        except:
            self.logger.error('Exchange connection problem!')
            sys.exit(56)
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

    def check_order_limits(self, order: dict):
        """
        :param order: Order dict
        :type order: dict
        :return: False if limits not passed, otherwise True
        :rtype: bool
        """
        symbol = order['symbol']
        order['cost'] = order['price'] * order['amount']
        limits = self.markets[symbol]['limits']
        for p, v in order.items():
            if p in limits.keys():
                min_v = limits[p]['min'] if limits[p]['min'] is not None else -float('Inf')
                max_v = limits[p]['max'] if limits[p]['max'] is not None else float('Inf')
                if not (min_v < v < max_v):
                    return False
        return True



        # cost = float(amount) * float(price)
        # for l, v in limits.items:
        #     if < v.max and
        # if limits['cost']['max'] > cost > limits['cost']['min']:
        #     return True
        # if limits['price']['max'] > price > limits['price']['min']:
        #     return True
        # if limits['amount']['max'] > amount > limits['amount']['min']:
        #     return True

        return False

    def place_multiple_orders(self, quotes: list):
        """
        Place multiple quotes and update order_history
        with response indexing by id or client_order_id

        :param quotes: Feed with quotes
        :type quotes: list
        """
        if not isinstance(quotes, list):
            return False
        if len(quotes) < 1:
            return False
        for q in quotes:
            response = self.create_order(**q)
            if isinstance(response, dict):
                if 'id' in response:
                    if response['id'] is not None:
                        self.order_history[response['id']] = response
                    elif response['id'] is None:
                        self.order_history[response['client_order_id']] = response
                else:
                    self.order_history[response['client_order_id']] = response

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
        :return: response from an exchange with order data or order_dict which status are exception name
        :rtype: dict
        """
        # Create random number
        if client_order_id is None:
            seed(time_ns())
            client_order_id = ''.join(["%s" % randint(0, 9) for _ in range(0, 9)])
        else:
            client_order_id = client_order_id
        if self.marketonly:
            order_type = 'MARKET'
        # Build order dict
        order_dict = dict(symbol=symbol, type=order_type,
                          side=side, amount=amount, price=price)
        # Check market filters before quoting
        if not self.check_order_limits(order_dict):
            order_dict['status'] = 'limits not passed'
            order_dict['timestamp'] = time_ns()
            order_dict['client_order_id'] = client_order_id
            return order_dict

        #On dry run return order_dict
        if self.dry_run:
            order_dict['status'] = 'DRY_RUN'
            order_dict['timestamp'] = time_ns()
            order_dict['client_order_id'] = client_order_id
            return order_dict

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

    def fetch_open_orders(self, markets: list):
        if not isinstance(markets, list):
            self.logger.error("Define markets for fetching open orders!")
            return 0
        for m in markets:
            try:
                resp = self.exchange.fetch_open_orders(m)
                self.order_history[resp['orderId']] = resp
            except Exception as e:
                self.logger.error('While fetching orders next error occur: ', type(e).__name__, "!!!", e.args)

    def fetch_processed_orders(self):
        """
        Update status or orders in order_history,
        on exception feed status with exception name
        """
        if len(self.order_history) == 0:
            return False
        for x, y in self.order_history.items():
            try:
                resp = self.exchange.fetch_order(y['id'], y['symbol'])
                self.order_history[x] = resp
            except Exception as e:
                self.order_history[x]['status'] = type(e).__name__

    def cancel_processed_orders(self):
        """
        Cancel all orders from order_history which status are 'open'
        """
        if len(self.order_history) == 0:
            return False
        for x, y in self.order_history.items():
            if y['status'] == 'open':
                try:
                    resp = self.exchange.fetch_order(y['id'], y['symbol'])
                    self.order_history[x] = resp
                except Exception as e:
                    self.order_history[x]['status'] = type(e).__name__

    def cancel_all_orders(self, symbol: str = None, orders: dict = None):
        if symbol is None and orders is None:
            self.logger.warning("Use with symbol or orders dict params!")
            return 0
        if orders is not None:
            for o in orders.values():
                self.exchange.cancel_order(o['id'])
        if symbol is not None:
            open_orders = self.exchange.fetch_open_orders(symbol=symbol)
            for o in open_orders.values():
                self.exchange.cancel_order(o['id'])


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
            sys.exit(56)

    # endregion

    # region OHLCV Candles

    def get_ohlcv(self, symbol, timeframe: str = '1h', limit: int = 200):
        """Fetch exchanges ticker for necessary pair, timeframe and length

        :param symbol: Symbol (i.e. BNB/BTC)
        :param timeframe: 1m, 5m...
        :param limit: default == max == 500
        :return: ccxt ohlcv dict
        :rtype: dict
        """
        try:
            response = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.logger.error("Exiting")
            sys.exit(56)
        return response

    def process_ohlcv(self, markets: list, time_frames: list = None, limit: int = 100):
        """Process multiple timeframes ohlcv data for markets in a list

        :type markets: list
        :type time_frames: list or None
        :type limit: int
        :return: Portfolio ohlcv dict
        :rtype: dict
        """
        if not isinstance(markets, list):
            return {}
        if len(markets) < 1:
            return {}
        if time_frames is None or not isinstance(time_frames, list):
            time_frames = ['1h', ]
        if not isinstance(limit, int):
            limit = 100
        if limit < 20:
            self.logger.warning("Minimum recommended limit is 20")
            limit = 20
        ptf = self.possible_timeframes
        intersection = [i for i in time_frames if i in ptf]
        if len(intersection) > 0:
            time_frames = intersection
        else:
            return {}
        portfolio_ohlcv = dict()
        for m in markets:
            portfolio_ohlcv[m] = {ptf[tf]: self.get_ohlcv(m, tf, limit) for tf in time_frames}
        return portfolio_ohlcv

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
        Fetch symbol ticker and update all_tickers dict

        :param symbol: market symbol
        """
        try:
            response = self.exchange.fetch_ticker(symbol)
            self.all_tickers[symbol] = response
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.logger.error("Exiting")
            sys.exit()

    # endregion
