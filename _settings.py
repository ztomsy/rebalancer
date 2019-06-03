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
    'USDT': (0.05, 0.9)}

########################################################################################################################
# Portfolio optimization settings
########################################################################################################################

WEIGHT_BOUNDS = (0.1, 0.8)

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
    'binance': {'window': ,
                'api_key': '',
                'secret': ''},
    'kucoin': {'api_key': '',
                'secret': ''}}

INFLUX_DATA = {'host': '',
               'port': ,
               'username': '',
               'password': '',
               'database': ''}

########################################################################################################################
# Misc Behavior, Technicals
########################################################################################################################

# If true, don't set up any orders, just say what we would do
DRY_RUN = True
# DRY_RUN = False

BUILD_DATE = '190601'

# How often to re-check and replace orders.
# Generally, it's safe to make this short if we're fetching
# from websockets. But if too many order amend/replaces are
# done, you may hit a ratelimit.
LOOP_INTERVAL = 5

# Wait times between orders / errors
API_REST_INTERVAL = 1
API_ERROR_INTERVAL = 10
TIMEOUT = 7

# If file changes, reload the bot.
WATCHED_FILE = '_settings'

########################################################################################################################
# Index settings
########################################################################################################################

# Index asset names
SCINDEX = ['USDT', 'TUSD', 'PAX', 'DAI', 'USDC', 'USDS', ]

