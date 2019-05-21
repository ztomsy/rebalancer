from os.path import join
import logging


########################################################################################################################
# Connection/Auth
########################################################################################################################

AUTH_DATA = {
    'binance': {'window': 100,
                'api_key': '',
                'secret': ''},
    'kucoin': {'api_key': '',
                'secret': 'cd1a2a1b--42f7-aa67-874aff11f069'}}

INFLUX_DATA = {'host': '',
               'port': 8086,
               'username': '',
               'password': '',
               'database': ''}


########################################################################################################################
# Index settings
########################################################################################################################

# Index asset names
SCINDEX = ['USDT', 'TUSD', 'PAX', 'DAI', 'USDC', 'USDS', ]

########################################################################################################################
# Portfolio settings
########################################################################################################################

# Specify the assets that you hold. These will be used in portfolio calculations.
PORTFOLIO = {
    'BTC': {'min': 10, 'max': 80},
    'USDT': {'min': 10, 'max': 80}, }



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
# Use to guarantee a maker rebate.
# However -- orders that would have matched immediately will instead cancel, and you may end up with
# unexpected delta. Be careful.
POST_ONLY = False

########################################################################################################################
# Misc Behavior, Technicals
########################################################################################################################

# If true, don't set up any orders, just say what we would do
DRY_RUN = True
# DRY_RUN = False

# How often to re-check and replace orders.
# Generally, it's safe to make this short because we're fetching from websockets. But if too many
# order amend/replaces are done, you may hit a ratelimit.
LOOP_INTERVAL = 5

# Wait times between orders / errors
API_REST_INTERVAL = 1
API_ERROR_INTERVAL = 10
TIMEOUT = 7

# Available levels: logging.(DEBUG|INFO|WARN|ERROR)
LOG_LEVEL = logging.DEBUG

# If any of these files (and this file) changes, reload the bot.
WATCHED_FILES = [join('core', '_settings'), join('payload', 'runner.py'), join('binance', 'restclient.py')]
