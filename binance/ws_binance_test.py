import binance.wsclient as binance
import asyncio
import time

binance.enable_logging(True)

api_key = ""
api_secret_key = ""


def orderbook():
    print("\nTesting orderbook data\n")

    stream = binance.Streamer()

    async def stop():
        await(asyncio.sleep(10))
        stream.close_all()
        asyncio.get_event_loop().stop()

    def on_order_book(data):
        ob = stream.get_order_book("ETHBTC")
        print(list(ob['asks'].items())[0], list(ob['bids'].items())[0])

    stream.add_order_book("ETHBTC", on_order_book)

    asyncio.Task(stop())

    asyncio.get_event_loop().run_forever()

def market_data():
    print("\nMarket data examples\n")

    print("Connection ok? ", binance.ping())

    print("Server time: ", binance.server_time())

    order_book = binance.order_book("BNBBTC", 5)
    print(order_book)


    print("Order book for BNB-BTC")
    print("asks")
    for (price, quantity) in order_book.asks:
        print(price, quantity)

    print("bids")
    for (price, quantity) in order_book.bids:
        print(price, quantity)


    print(binance.aggregate_trades("BNBBTC", limit=5))

    candles = binance.candlesticks("BNBBTC", "1m")
    print(candles)

    print("Current ticker prices")
    prices = binance.ticker_prices()
    print(prices)

    print("Current ticker for order books")
    order_books = binance.ticker_order_books()
    print(order_books["ETHBTC"])

    print("Order book ticker for ETHBTC")
    book = order_books["ETHBTC"]
    print(book)

    print("Order book ticker for BNBBTC")
    book = order_books["BNBBTC"]
    print(book)


    last_24hr = binance.ticker_24hr("BNBBTC")
    print(last_24hr)

def account():
    print("\nAccount data examples\n")

    account = binance.Account(api_key, api_secret_key)

    account.set_receive_window(5000)

    new_order = account.new_order("ETHBTC", "BUY", "LIMIT", .1, 0.01)
    new_order_id = new_order["orderId"]
    print("new order id = ", new_order_id)

    order = account.query_order("ETHBTC", new_order_id)
    print(order)

    order = account.cancel_order("ETHBTC", new_order_id)
    print(order)

    open_orders = account.open_orders("ETHBTC")
    print(open_orders)

    all_orders = account.all_orders("ETHBTC")
    print(all_orders)

    info = account.account_info()
    print(info)

    trades = account.my_trades("ETHBTC")
    print(trades)

def user_stream():
    print("\nUser Stream examples\n")

    stream = binance.Streamer()

    async def stop():
        await(asyncio.sleep(5))
        stream.close_all()
        asyncio.get_event_loop().stop()

    def on_user_data(data):
        print("new user data: ", data)

    stream.start_user(api_key, on_user_data)

    asyncio.Task(stop())

    asyncio.get_event_loop().run_forever()

def data_streams():
    print("\nData Stream examples\n")

    stream = binance.Streamer()

    async def stop():
        await(asyncio.sleep(5))
        stream.close_all()
        asyncio.get_event_loop().stop()

    def on_order_book(data):
        print("order book changes - ", data)

    stream.add_order_book("ETHBTC", on_order_book)

    def on_candlestick(data):
        print("new candlesticks - ", data)
        print("all candlesticks- ", stream.get_candlesticks("ETHBTC"))

    def on_trades(data):
        print("trade update - ", data)

    asyncio.Task(stop())

    asyncio.get_event_loop().run_forever()

orderbook()
# market_data()
# account()
# user_stream()
# data_streams()
