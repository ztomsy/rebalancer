import urllib.request
import urllib.parse
import json
import datetime
import hmac
import hashlib
import time
import asyncio
import websockets
from decimal import Decimal
from collections import namedtuple


__URL_BASE = "https://www.binance.com/api/"
__log_enabled = False



def tets():
    return None

def __timestamp():
    return int(round(time.time() * 1000))


def __v1_url(endpoint):
    return __URL_BASE + "v1/" + endpoint


def __v3_url(endpoint):
    return __URL_BASE + "v3/" + endpoint


def _log(msg):
    global __log_enabled
    if __log_enabled:
        print(msg)


_URLS = {
    # General
    "ping": __v1_url("ping"),
    "time": __v1_url("time"),

    # Market Data
    "depth": __v1_url("depth"),
    "agg_trades": __v1_url("aggTrades"),
    "candlesticks": __v1_url("klines"),
    "ticker_prices":  __v1_url("ticker/allPrices"),
    "ticker_books": __v1_url("ticker/allBookTickers"),
    "ticker_24hr": __v1_url("/ticker/24hr"),

    # Account
    "user_data_stream": __v1_url("userDataStream"),
    "order": __v3_url("order"),
    "open_orders": __v3_url("openOrders"),
    "all_orders": __v3_url("allOrders"),
    "account": __v3_url("account"),
    "my_trades": __v3_url("myTrades")
}

OrderBook = namedtuple("OrderBook", "bids asks")

OrderBookTicker = namedtuple("OrderBookTicker", "bid_price, bid_qty, ask_price, ask_qty")

CandleStick = namedtuple("CandleStick", "open_time open high low close volume close_time quote_asset_volume trade_count taker_buy_base_quote_vol taker_buy_quote_asset_vol")


def _geturl_json(url, query_params={}, sign=False, method="GET", api_key=None, api_secret_key=None):
    if query_params is not None:
        for key in list(query_params.keys()):
            if query_params[key] is None:
                del query_params[key]

        if sign:
            query_params["timestamp"] = __timestamp()
            query = urllib.parse.urlencode(query_params)
            query_params["signature"] = hmac.new(api_secret_key.encode("utf8"), query.encode("utf8"), digestmod=hashlib.sha256).hexdigest()

        url += "?" + urllib.parse.urlencode(query_params)

    _log(method + ": " + url)

    req = urllib.request.Request(url, method=method)

    if api_key:
        req.add_header("X-MBX-APIKEY", api_key)

    json_ret = {}

    try:
        resp = urllib.request.urlopen(req)
        json_ret = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        data = e.read()
        raise Exception("Request Failed: " + str(data))

    return json_ret


def enable_logging(enabled):
    """ Enable or Disable logging
    :param enabled: True to turn logging on, false to turn it off
    """

    global __log_enabled
    __log_enabled = enabled

    print("Logging", "enabled" if enabled else "disabled")


# Public API (no authentication required)


def ping():
    """ Ping Binance.com to see if it's online and we can hit it
    :return: True if pint was success, False otherwise
    """

    return _geturl_json(_URLS["ping"]) == {}


def server_time():
    """
    Get the current server time
    :return: Datetime object with the current server time
    """
    data = _geturl_json(_URLS["time"])
    return datetime.datetime.fromtimestamp(data["serverTime"] / 1000.0)


def order_book(symbol, limit=None):
    """ Get the order book for a given market symbol

    :param symbol: The market symbol (ie: BNBBTC)
    :param limit: (default 100, max 100, optional)
    :return: OrderBook tuple instance, containing the bids and asks
    """

    data = _geturl_json(_URLS["depth"], {"symbol": symbol, "limit": limit})

    bids = []
    asks = []
    for bid in data["bids"]:
        price_qty = (Decimal(bid[0]), Decimal(bid[1]))
        bids.append(price_qty)

    for ask in data["asks"]:
        price_qty = (Decimal(ask[0]), Decimal(ask[1]))
        asks.append(price_qty)

    book = OrderBook(bids, asks)

    return book


def aggregate_trades(symbol, from_id=None, start_time=None, end_time=None, limit=None):
    """ Get compressed, aggregate trades. Trades that fill at the time, from the same order,
    with the same price will have the quantity aggregated.

    If both startTime and endTime are sent, limit should not be sent AND the distance between
    startTime and endTime must be less than 24 hours.

    :param symbol: The market symbol (ie: BNBBTC)
    :param from_id: ID to get aggregate trades from INCLUSIVE (optional)
    :param start_time: Timestamp in ms to get aggregate trades from INCLUSIVE (optional)
    :param end_time: Timestamp in ms to get aggregate trades until INCLUSIVE (optional)
    :param limit: (Default 500; max 500, optional)
    :return:
    """

    params = {
        "symbol": symbol,
        "fromId": from_id,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit}

    trades = _geturl_json(_URLS["agg_trades"], params)

    # convert price and quantity to decimals
    for trade in trades:
        trade["p"] = Decimal(trade["p"])
        trade["q"] = Decimal(trade["q"])

    return trades


def candlesticks(symbol, interval, limit=None, start_time=None, end_time=None):
    """ Get Kline/candlestick bars for a symbol.
    Klines are uniquely identified by their open time.

    :param symbol: The market symbol (ie: BNBBTC)
    :param interval: one of (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
    :param limit: number of entries to return (Default 500; max 500, optional)
    :param start_time: Timestamp in ms to get candles from INCLUSIVE (optional)
    :param end_time: Timestamp in ms to get candles until INCLUSIVE(optional)
    :return: an array of CandleStick tuples
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_time,
        "endTime": end_time
    }

    candles = _geturl_json(_URLS["candlesticks"], params)
    for i in range(len(candles)):
        candles[i] = candles[i][:-1]
        for j in range(len(candles[i])):
            if isinstance(candles[i][j], str):
                candles[i][j] = Decimal(candles[i][j])

        candles[i] = CandleStick(*candles[i])

    return candles


def ticker_prices():
    """ Get the latest prices for all market symbols
    :return: a dict mapping the market symbols to prices
    """

    coins = _geturl_json(_URLS["ticker_prices"])

    prices = {}
    for coin in coins:
        prices[coin["symbol"]] = Decimal(coin["price"])

    return prices


def ticker_order_books():
    """ Gets the best price/quantity on the order book for all market symbols
    :return: an array of OrderBookTicker tuples (bid_price, bid_qty, ask_price, ask_qty)
    """
    coins = _geturl_json(_URLS["ticker_books"])

    book_tickers = {}
    for coin in coins:
        book_tickers[coin["symbol"]] = {
            OrderBookTicker(
                Decimal(coin["bidPrice"]),
                Decimal(coin["bidQty"]),
                Decimal(coin["askPrice"]),
                Decimal(coin["askQty"])
            )
        }

    return book_tickers


def ticker_24hr(symbol):
    """
    Gets the 24 hour price change statistics for a give market symbol
    :param symbol: the market symbol (ie: BNBBTC)
    :return: a dict containing statistics for the last 24 hour period
    """

    ticker = _geturl_json(_URLS["ticker_24hr"], {"symbol": symbol})

    # wrap float from string into decimal, leave int and symbol key unwrapped
    for key in ticker:
        if isinstance(ticker[key], str) and key!='symbol':
            ticker[key] = Decimal(ticker[key])

    return ticker


# Private signed method access is provided through the Account class
class Account:
    def __init__(self, key, secret):
        """ create a new accuont and set set the API key and the API secret Key
        If you don't have a key, log into binance.com and create one at https://www.binance.com/userCenter/createApi.html
        Be sure to never commit your keys to source control

        :param key: The API Key from your Binance account
        :param secret: The API Secret Key from your Binance account (case sensitive)
        """
        self.__recv_window = None
        self.__api_key = key
        self.__api_secret_key = secret
        self.__recv_window = None

    def set_receive_window(self, window_millis):
        """ specify the number of milliseconds a request must be processed within
        before being rejected by the server. If not set, the default is 5000 ms

        :param window_millis: the number of milliseconds after timestamp the request is valid for
        """

        self.__recv_window = window_millis

    def new_order(self, symbol, side, type, quantity, price=0, new_client_order_id=None, stop_price=None, iceberg_qty=None):
        """ Submit a new order

        :param symbol: the market symbol (ie: BNBBTC)
        :param side: "BUY" or "SELL"
        :param type: "LIMIT" or "MARKET"
        :param quantity: the amount to buy/sell
        :param price: the price to buy/sell at
        :param new_client_order_id: A unique id for the order. Automatically generated if not sent (optional)
        :param stop_price: Used with stop orders (optional)
        :param iceberg_qty: Used with iceberg orders (optional)
        :return: new order id
        """

        params = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price,
            "newClientOrderId": new_client_order_id,
            "stopPrice": stop_price,
            "icebergQty": iceberg_qty,
            "recvWindow": self.__recv_window
        }

        return _geturl_json(_URLS["order"], params, True, "POST", api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def query_order(self, symbol, order_id=None, orig_client_order_id=None):
        """ Check an order's status
        Either order_id or orig_client_order_id must be sent

        :param symbol: the market symbol (ie: BNBBTC)
        :param order_id: the order id if orig_client_order_id isn't known
        :param orig_client_order_id: the client order id, if order id isn't known
        :return: a dict containing information about the order, if found
        """

        if order_id is None and orig_client_order_id is None:
            raise Exception("param Error: must specify orderId or origClientOrderId")

        params = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
            "recvWindow": self.__recv_window
        }

        return _geturl_json(_URLS["order"], params, True, api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None, new_client_order_id=None):
        """ Cancel an active order
        Either order_id or orig_client_order_id must be sent

        :param symbol: the market symbol (ie: BNBBTC):
        :param order_id: the order id if orig_client_order_id isn't known
        :param orig_client_order_id: the client order id, if order id isn't known
        :param new_client_order_id: Used to uniquely identify this cancel. Automatically generated by default (optiona)
        :return: a dict containing information about the cancelled order, if it existed
        """

        if order_id is None and orig_client_order_id is None:
            raise Exception("param Error: must specify orderId or origClientOrderId")

        params = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
            "newClientOrderId": new_client_order_id,
            "recvWindow": self.__recv_window
        }

        return _geturl_json(_URLS["order"], params, True, method="DELETE", api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def open_orders(self, symbol):
        """ Gets all the open orders for a given symbol

        :param symbol: the market symbol (ie: BNBBTC)
        :return: an array of dicts containing info about all the open orders
        """

        return _geturl_json(_URLS["open_orders"], {"symbol": symbol}, True, api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def all_orders(self, symbol, order_id=None, limit=None):
        """ Get all account orders; active, canceled, or filled

        :param symbol: the market symbol (ie: BNBBTC)
        :param order_id: if set, it will get orders >= that orderId. Otherwise most recent orders are returned (optional)
        :param limit: the limit of orders to return (Default 500; max 500, optinal))
        :return: an array of dicts containing info about all the open orders
        """
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "limit": limit
        }

        return _geturl_json(_URLS["all_orders"], params, True, api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def account_info(self):
        """ gets account information
        :return: dict containing account information and all balances
        """
        return _geturl_json(_URLS["account"], sign=True, api_key=self.__api_key, api_secret_key=self.__api_secret_key)

    def my_trades(self, symbol, limit=None, from_id=None):
        """ Get trades for a specific account and symbol

        :param symbol: te market symbol (ie: BNBBTC)
        :param limit: the max number of trades to get (Default 500; max 500, optional)
        :param from_id: TradeId to fetch from. Default gets most recent trades (optional)
        :return: an array of dicts containing the trade info
        """
        params = {
            "symbol": symbol,
            "limit": limit,
            "fromId": from_id
        }

        return _geturl_json(_URLS["my_trades"], params, True, api_key=self.__api_key, api_secret_key=self.__api_secret_key)


class Streamer:
    def __init__(self):
        self.__open_sockets = set()
        self.__pending_reads = {}
        self.__order_books = {}
        self.__candlesticks = {}
        self.__trades = {}
        self.__user_listen_key = ""
        self.__api_key = ""
        self.__keep_alive_task = None
        self.__keep_alive_timer = None

    async def __run(self, url, id, callback):
        if id in self.__open_sockets:
            _log("Socket already opened for id: " + id)
            return

        _log("Opening stream - " + url)

        async with websockets.connect(url) as socket:
            self.__open_sockets.add(id)

            while id in self.__open_sockets:
                recv_task = asyncio.Task(socket.recv())

                self.__pending_reads[id] = recv_task
                data = await recv_task
                data = json.loads(data)
                del self.__pending_reads[id]

                symbol = data["s"]
                if id.find("depth") == 0:
                    self.__update_order_book(symbol, data)
                elif id.find("kline") == 0:
                    if self.__candlesticks[symbol] == None:
                        self.__candlesticks[symbol] = []
                    self.__candlesticks[symbol].append(data["k"])
                elif id.find("trades") == 0:
                    if self.__trades[symbol] == None:
                        self.__trades[symbol] = []
                    self.__trades[symbol].append(data)

                callback(data)
                await(asyncio.sleep(.00001))

    def __update_order_book(self, symbol, changes):
        book = self.__order_books[symbol]

        if len(book["bids"]) == 0 and len(book["asks"]) == 0:
            initial_orders = order_book(symbol)
            for (p, q) in initial_orders.bids:
                book["bids"][p] = q
            for (p, q) in initial_orders.asks:
                book["bids"][p] = q

        bids = changes["b"]
        for bid in bids:
            price = Decimal(bid[0])
            quantity = Decimal(bid[1])
            bids = book["bids"]

            if quantity > 0:
                bids[price] = quantity
            elif price in bids:
                del bids[price]

        asks = changes["a"]
        for ask in asks:
            price = Decimal(ask[0])
            quantity = Decimal(ask[1])
            asks = book["asks"]

            if quantity > 0:
                asks[price] = quantity
            elif price in asks:
                del asks[price]

    def start_user(self, api_key, callback):
        """ Start the user data stream. After it's open, it will automatically send a keep alive request every 30 seconds
        :param api_key:
        :param callback: function to call when new user data comes in
        """

        self.__api_key = api_key

        data = _geturl_json(_URLS["user_data_stream"], {}, method="POST", api_key=api_key)
        self.__user_listen_key = data["listenKey"]
        stream_url = "wss://stream.binance.com: 9443/ws/" + self.__user_listen_key

        asyncio.Task(self.__run(stream_url, "user_" + self.__user_listen_key, callback))
        self.__keep_alive_task = asyncio.Task(self.__keep_alive_user(callback))

    async def __keep_alive_user(self, callback):
        while True:
            _log("User data stream keep alive heartbeat")

            _geturl_json(_URLS["user_data_stream"], {"listenKey": self.__user_listen_key}, method="PUT", api_key=self.__api_key)
            self.__keep_alive_timer = await(asyncio.sleep(30))

    def close_user(self):
        """ Close the user data stream
        """
        _log("Closing user data stream")

        self.__keep_alive_task.cancel()
        self.__keep_alive_timer.cancel()
        self.__close("user_" + self.__user_listen_key)
        _geturl_json(_URLS["user_data_stream"], {"listenKey": self.__user_listen_key}, method="DELETE", api_key=self.__api_key)

        self.__user_listen_key = ""
        self.__api_key = ""
        self.__keep_alive_task = None

    def add_order_book(self, symbol, callback):
        """ Open an order book stream
        :param symbol: the market symbol (ie: BNBBTC)
        :param callback: a function to call when new data comes in
        """

        self.__order_books[symbol] = {"bids": {}, "asks": {}}
        url = "wss://stream.binance.com:9443/ws/" + symbol.lower() + "@depth"
        asyncio.Task(self.__run(url, "depth_" + symbol, callback))

    def get_order_book(self, symbol):
        """ Returns the currently cached order book
        :param symbol: the market symbol (ie: BNBBTC)
        :return: current order book data
        """
        return self.__order_books[symbol]

    def add_candlesticks(self, symbol, interval, callback):
        """ Open a candlestick stream
        :param symbol: the market symbol (ie: BNBBTC)
        :param interval: one of (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        :param callback: a function to call when new data comes in
        """

        self.__candlesticks[symbol] = []
        url = "wss://stream.binance.com:9443/ws/" + symbol.lower() + "@kline_" + interval
        asyncio.Task(self.__run(url, "kline_" + symbol + "_" + str(interval), callback))

    def get_candlesticks(self, symbol):
        """ Returns the currently cached candlesticks
        :param symbol: the market symbol (ie: BNBBTC)
        :return: current candlestick data
        """
        return self.__candlesticks[symbol]

    def add_trades(self, symbol, callback):
        """ Open an aggregated trades stream
        :param symbol: the market symbol (ie: BNBBTC)
        :param callback: a function to call when new data comes in
        """
        url = "wss://stream.binance.com:9443/ws/" + symbol.lower() + "@aggTrades"
        asyncio.Task(self.__run(url, "trades" + symbol, callback))

    def get_trades(self, symbol):
        """ Returns the currently cached trades
        :param symbol: the market symbol (ie: BNBBTC)
        :return: current trade data
        """
        return self.__trades[symbol]

    def remove_order_book(self, symbol):
        """ Close an order book stream
        :param symbol: the market symbol (ie: BNBBTC)
        """
        del self.__order_books[symbol]
        self.__close("depth_" + symbol)

    def remove_candlesticks(self, symbol, interval):
        """ Close a candlestick stream
        :param symbol: the market symbol (ie: BNBBTC)
        :param interval: one of (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        """

        del self.__candlesticks[symbol]
        self.__close("kline_" + symbol + "_" + str(interval))

    def remove_trades(self, symbol):
        """ Close a trades stream
        :param symbol: the market symbol (ie: BNBBTC)
        """

        self.__close("trades_" + symbol)

    def __close(self, id):
        _log("Closing stream: " + id)

        if id not in self.__open_sockets:
            _log("Can't close stream, not open")
            return

        self.__open_sockets.remove(id)
        self.__pending_reads[id].cancel()
        del self.__pending_reads[id]

        _log("Stream closed: ", id)

    def close_all(self):
        """
        close all the streams and stop the event loop
        """
        _log("closing all streams")

        for key in self.__pending_reads:
            self.__pending_reads[key].cancel()

        self.__open_sockets.clear()

