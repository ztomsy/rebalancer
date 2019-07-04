
########################################################################################################################
# Portfolio settings
########################################################################################################################

# Specify base asset for portfolio calculation such as for example: 'BTC' or 'USDT'
PORTFOLIO_BASE_ASSET = 'USDT'

# Specify the assets that you hold. These will be used in portfolio calculations.
PORTFOLIO = {
    'BTC': (0.05, 0.9),
    'ETH': (0.05, 0.9),
    'BNB': (0.05, 0.9),
    # 'USDT': (0.05, 0.9),
    # 'TRX': (0, 1),
    # 'OMG': (0, 1),
    # 'ZRX': (0, 1),
    # 'REP': (0, 1),
    # 'VET': (0, 1),
    # 'ICX': (0, 1),
    # 'ZIL': (0, 1),
    # 'AE': (0, 1),
    }


########################################################################################################################
# Portfolio optimization settings
########################################################################################################################

WEIGHT_BOUNDS = (0.05, 0.99)

# Use this settings to define portfolio optimization behaviour
# Choose only one of next option at the same time
TARGET_RETURN = 0.05

TARGET_RISK = None

# Rebalancing precision as percent.
# This parameter can change all behaviour undo all small moving
REBALANCING_PRECISION = 0.01

########################################################################################################################
# Order Size & Spread
########################################################################################################################

# How many pairs of buy/sell orders to keep open
ORDER_PAIRS = 6

# Distance between successive orders, as a percentage (example: 0.005 for 0.5%)
INTERVAL = 0.005

########################################################################################################################
# Trading Behavior
########################################################################################################################

# If True, will only send orders that rest in the book.
# However -- orders that would have matched immediately
# will always lead to unexpected price and fee, and you
# may end up with unexpected delta. Be careful.
MARKET_ONLY = False

########################################################################################################################
# Connection/Auth
########################################################################################################################

AUTH_DATA = {
    'binance': {'window': 100,
                'api_key': '',
                'secret': ''},
    'kucoin': {'api_key': '',
                'secret': ''}}

INFLUX_DATA = {'host': '',
               'port': 8086,
               'username': '',
               'password': '',
               'database': ''}

########################################################################################################################
# Misc Behavior, Technicals
########################################################################################################################

# If true, don't set up any orders, just say what we would do
DRY_RUN = True
# DRY_RUN = False

# Fetched and displayed timeframes are controlled by this list, first value is used for displaying
TIME_FRAMES = ['1h', ]
# TIME_FRAMES = ['1h', '1m']

# How often to re-check and replace orders.
# Generally, it's safe to make this short if we're fetching
# from web sockets.
LOOP_INTERVAL = (40, 60)

# Wait times between orders / errors
API_REST_INTERVAL = 1
API_ERROR_INTERVAL = 10
TIMEOUT = 7

# If file changes, reload the bot.
WATCHED_FILE = 'settings.py'

BUILD_DATE = '190704'

