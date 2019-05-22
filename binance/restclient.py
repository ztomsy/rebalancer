#!/usr/bin/env python
# encoding: utf-8
import ccxt
import sys
from time import time_ns

from core.shared import Side, OType
from core.core import rounded_to_precision
from payload.orderbook import Orderbook

class RestClient:

    def __init__(self, window: int = 100, api_key: str = None, secret: str = None,
                 verbose: bool = False, logger: object = None):
        '''
        Exchange initialising
        '''
        self.logger = logger
        self.exchange_name = 'binance'
        self._secret = secret
        self._api_key = api_key
        self.exchange = ccxt.binance({"apiKey": self._api_key,
                                      "secret": self._secret,
                                      'verbose': verbose})  # type: ccxt.binance

        # Initialize the Orderbook with a set of empty dicts and other defaults
        self.orderbook = Orderbook(window, logger)

        # Load markets on initialization
        self.markets = self.exchange.load_markets()

        self.all_tickers = {}

        # Order and trade sets
        self.confirm_trade_collector = []
        self._order_index = 0
        self.order_history = []
        self._ex_index = 0
        self._lookup = {}

        self._candlesticks = dict()
        self._trades = dict()

        self.balances = list()

    # region Order
    def create_order(self, symbol, side: Side, order_type: OType, quantity, price=None, new_client_order_id=None,
                     stop_price=None,
                  iceberg_qty=None):
        """ Submit a new order

        :param symbol: the market symbol (ie: BNBBTC)
        :param side: "BUY" or "SELL"
        :param order_type: "LIMIT" or "MARKET"
        :param quantity: the amount to buy/sell
        :param price: the price to buy/sell at, used in LIMIT order type
        :param new_client_order_id: A unique id for the order. Automatically generated if not sent (optional)
        :param stop_price: Used with stop orders (optional)
        :param iceberg_qty: Used with iceberg orders (optional)
        :return: response from an exchange with order data(orderID, etc.)
        """
        try:
            order_c = self.exchange.create_order(symbol=symbol,
                                                 type=order_type,
                                                 side=side,
                                                 amount=quantity,
                                                 price=price,
                                                 timeInForce="GTC",  # 'GTC' = Good Till Cancel(default), 'IOC' = Immediate Or Cancel
                                                 stopPrice=stop_price,
                                                 iceberQty=iceberg_qty)
            return order_c
        except Exception as e:
            # print(type(e).__name__, e.args, str(e))
            print('While creating order next error occur: ', type(e).__name__, "!!!", e.args)
            print("Exiting")
            sys.exit()

    def add_order_to_history(self, order):
        '''Add an order (dict) to order_history'''
        self._order_index += 1
        self.order_history.append(
            {'exid': self._order_index, 'order_id': order['order_id'], 'timestamp': order['timestamp'],
             'type': order['type'], 'quantity': order['quantity'],
             'side': order['side'], 'price': order['price']})

    def _add_order_to_lookup(self, trader_id, order_id, ex_id):
        '''
        Add lookup for ex_id
        '''
        if trader_id in self._lookup.keys():
            self._lookup[trader_id][order_id] = ex_id
        else:
            self._lookup[trader_id] = {order_id: ex_id}

    # endregion

    # region Balance

    @staticmethod
    def _filter_not_null(balances):
        filtered_balances = {}
        for x in balances['info']['balances']:
            if (float(x['free']) > 0) or (float(x['locked']) > 0):
                filtered_balances[x['asset']] = {'free': x['free'],
                                                 'locked': x['locked'],
                                                 'all': float(x['free'])+ float(x['locked'])}
        return filtered_balances

    def fetch_balances(self):
        '''
        Fetch presented balances
        :return:
        '''
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

    def get_ohlcv(self, symbol, timeframe='1m', limit=100):
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
            spread_p = rounded_to_precision(100 * spread / mid_price, 4)
            # Update all_tickers with new data
            self.all_tickers[s]['mid_price'] = mid_price
            self.all_tickers[s]['spread'] = spread
            self.all_tickers[s]['spread_p'] = spread_p
            self.all_tickers[s]['timestamp'] = time_ns()

    def process_tickers(self, tickers: list = None):
        self.get_all_tickers()
        self.calc_tickers(tickers)

    def get_all_tickers(self):
        # Fetch exchanges tickers for all pairs
        try:
            response = self.exchange.fetch_bids_asks()
            self.all_tickers.clear()
            self.all_tickers = response
        except Exception as e:
            self.logger.error("While fetching ohlcv next error occur: {}\n{}\n".format(type(e).__name__, e.args))
            self.logger.error("Exiting")
            sys.exit()

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