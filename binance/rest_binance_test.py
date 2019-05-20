from binance.restclient import RestClient as binance
import asyncio
import time

api_key = ""
api_secret_key = ""


def orderbook():
    print("\nTesting orderbook data\n")

    # Initialize client
    client = binance(api_key,api_secret_key)

    tt = 0

    for i in range(10):
        # Fetch ob data from an exchange and fill init lists
        tic = time.time()
        client.fetch_ob("BNB/BTC")
        ct = time.time() - tic
        tt = tt + ct
        # Print with class method
        #print(client.get_last_tob())
        print("{} iteration take {} time.".format(i, ct))
    print("\nMean iteration time was {} time.".format(tt/10))

def market_data():
    print("\nMarket data examples\n")

    # Initialize client
    client = binance(api_key, api_secret_key)

    # Get loaded on initialization markets
    print("Markets:{}".format(client.markets))

    # Get last top of order book for a symbol
    client.fetch_ob("BNB/BTC", limit=5)
    print("BNB/BTC top of book:", client.get_last_tob)

    # Get full ob data
    print("Order book for BNB-BTC")
    print("asks")
    for (price, quantity) in client._ask_book:
        print(price, quantity)

    print("bids")
    for (price, quantity) in client._bid_book:
        print(price, quantity)

    # 1m candles for "BNB/BTC"
    candles = client.get_ohlcv(symbol="BNB/BTC", timeframe='1m')
    print(candles)

    # Get all binance tickers
    tickers = client.get_all_tickers()
    print(tickers["BNB/BTC"])

def account():
    print("\nAccount data examples\n")

    # Initialize client
    client = binance(api_key,api_secret_key)

    # Get balance of BNB/BTC
    balances = client.get_balances()
    print("BNB balance", balances['BNB']['total'])
    print("BTC balance", balances['BTC']['total'])

    # new_order = account.new_order("ETHBTC", "BUY", "LIMIT", .1, 0.01)
    # new_order_id = new_order["orderId"]
    # print("new order id = ", new_order_id)
    #
    # order = account.query_order("ETHBTC", new_order_id)
    # print(order)
    #
    # order = account.cancel_order("ETHBTC", new_order_id)
    # print(order)
    #
    # open_orders = account.open_orders("ETHBTC")
    # print(open_orders)
    #
    # all_orders = account.all_orders("ETHBTC")
    # print(all_orders)
    #
    # info = account.account_info()
    # print(info)
    #
    # trades = account.my_trades("ETHBTC")
    # print(trades)


# orderbook()
# market_data()
# account()

