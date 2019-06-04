#!/usr/bin/env python
# encoding: utf-8

from time import sleep, time_ns, time, ctime
from sys import exit
from random import randrange, seed

from binance.restclient import RestClient as binanceRestClient
from payload.trader import Trader
from yat.uicurses import uiCurses, curses
from yat.influx import Influx
from yat.calcus import rounded_to_precision
from payload.portfolioOpt import PortfolioOpt


class Runner(object):
    """
    Init and run main loop
    >>>r=Runner
    >>>r.balances = {}
    >>>r._count_base_balance('')



    """

    def __init__(self, logger: object = None, watcher: object = None, **kwargs):
        """
        Init counter and enable logging
        """
        self.logger = logger
        self.file_watcher = watcher
        self.file_watcher.look()
        self.last_fetch_time = int(time())
        self.dry_run = kwargs['DRY_RUN']
        self.loop_interval = kwargs['LOOP_INTERVAL']
        self.market_only = kwargs['MARKET_ONLY']
        # Init screen with ui
        self.ui = uiCurses()
        self.ui.print_ui()
        self.ui.header_str = "Portfolio ReBalancer build:{}".format(kwargs['BUILD_DATE'])
        # Init database connection
        self.influx = Influx(kwargs['INFLUX_DATA'])
        # Init portfolio
        self.portfolio = kwargs['PORTFOLIO']
        # Init index values
        self.scindex = [_ for _ in self.portfolio.keys()]
        self.rebalancing_precision = kwargs['REBALANCING_PRECISION']
        self.portfolio_base_asset = kwargs['PORTFOLIO_BASE_ASSET']
        self.portfolio_base_amount: float = 0
        self.portfolio_assets = [x for x in self.portfolio.keys()]
        self.portfolio_weight_bounds = kwargs['WEIGHT_BOUNDS']
        self.portfolio_target_return = kwargs['TARGET_RETURN']
        self.portfolio_target_risk = kwargs['TARGET_RISK']
        self.portfolio_ohlcv = {}
        self.portfolio_current_weights = {}
        self.portfolio_recommended_weights = {}
        self.portfolio_difference = {}
        # Quote collector container
        self.quote_collector = []

        self.run_step = 0
        self.balances = {}

        # Initialise exchanges
        self.data_provider_list = []
        self.exchange = binanceRestClient(window=kwargs['AUTH_DATA']['binance']['window'],
                                          api_key=kwargs['AUTH_DATA']['binance']['api_key'],
                                          secret=kwargs['AUTH_DATA']['binance']['secret'],
                                          verbose=False,
                                          logger=logger,
                                          marketonly=self.market_only)
        self.data_provider_list.append(self.exchange.exchange_name)
        # self.data_provider_list.append([self.exchange.exchange_name, self.exchange])
        # Load index markets
        # self.scindex_markets = [x for x, y in self.exchange.markets.items() if (y['base'] in self.scindex and y[
        #     'quote'] == 'BTC') or (y['quote'] in self.scindex and y['base'] == 'BTC')]
        # Get all tickers
        self.exchange.process_tickers()

        self.portfolio_base_markets = [x for x, y in self.exchange.markets.items() if (y['base'] in self.portfolio_assets
                                                                                       and y['quote'] ==
                                                                                       self.portfolio_base_asset) or (y['quote'] in self.portfolio_assets
                                                                                        and y['base'] ==
                                                                                        self.portfolio_base_asset)]
        self.exchange.calc_tickers(self.portfolio_base_markets)

        # Run main loop and close threads on exit
        try:
            self.run_balancer()
        finally:
            try:
                curses.endwin()
                # self.logger.info("Closing curses")
            finally:
                pass
            # self.logger.info("Shutdown application")
            # self.exchange2.execute.shutdown()
            # self.exchange.order_history_to_pickle(self.cache_path)

    # region Index data
    def _update_index_data(self):
        self.ui.index_data.clear()
        self.ui.index_data = [['NAME', 'PROVIDER', 'TOB ASK', 'TOB BID', 'MID', 'SPREAD', 'SPREAD%'], ]
        for s in self.portfolio_base_markets:
            ticker = self.exchange.all_tickers[s]
            self.ui.index_data.append([s, self.exchange.exchange_name,
                                       "{:.2f}".format(ticker['ask']),
                                       "{:.2f}".format(ticker['bid']),
                                       "{:.2f}".format(ticker['mid_price']),
                                       "{:.2f}".format(ticker['spread']),
                                       "{:.4f}".format(ticker['spread_p'])])
    # endregion

    # region Portfolio data
    def _count_btc_balance(self, amount, asset):
        # asset not BTC
        # define BTC market
        for m in self.portfolio_base_markets:
            if asset in m:
                if 'BTC' in m:
                    if asset == 'USDT':
                        return amount/self.portfolio_ohlcv[m][-1][4]
                    else:
                        return amount*self.portfolio_ohlcv[m][-1][4]

    def _count_symbol_amount(self, symbol_base, amount):
        """
        Count amount of symbol_base currency from portfolio_base_asset amount
        :return: amount quoted in symbol_base asset
        :rtype: float
        """
        amount = amount
        ra = amount / self.exchange.all_tickers["{}/{}".format(symbol_base, self.portfolio_base_asset)]['ask']
        return ra

    def _count_base_balance(self, asset: str) -> float:
        """
        Count asset in portfolio_base_asset amount.

        :param asset: asset name
        :type asset: str
        :return: amount counted in base asset price
        :rtype: float
        """
        try:
            if asset == self.portfolio_base_asset:
                base_balance = self.balances[asset]['all']
            elif asset == 'USDT':
                base_balance = self.balances[asset]['all'] / self.portfolio_ohlcv[
                    "{}/{}".format(self.portfolio_base_asset, asset)][-1][4]
            else:
                base_balance = self.balances[asset]['all'] * self.portfolio_ohlcv[
                    "{}/{}".format(asset, self.portfolio_base_asset)][-1][4]
            return base_balance
        except KeyError:
            return 0.0

    def _count_portfolio_base_amount(self):
        pbv = 0
        for c in self.portfolio_assets:
            pbv += self._count_base_balance(c)
        self.portfolio_base_amount = pbv

    def _update_portfolio_current_weights(self):
        self.portfolio_current_weights.clear()
        for c in self.portfolio_assets:
            base_balance = float(self._count_base_balance(c))
            self.portfolio_current_weights[c] = base_balance/self.portfolio_base_amount

    def _update_portfolio_data(self):
        self.ui.portfolio_data.clear()
        self.ui.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'BASEPRICE', 'CURRENT%', 'RECOMMEND%', 'DIF%'], ]
        for c in self.portfolio_assets:
            try:
                balance_all = self.balances[c]['all']
            except KeyError:
                balance_all = 0
            base_balance = float(self._count_base_balance(c))
            try:
                bp = base_balance / self.portfolio_base_amount
            except ZeroDivisionError:
                bp = 0
            try:
                recw = self.portfolio_recommended_weights[c]
                difw = self.portfolio_difference[c]
            except KeyError:
                recw = 0
                difw = 0
            self.ui.portfolio_data.append([c, self.exchange.exchange_name,
                                           "{:.4f}".format(balance_all),
                                           "{:.2f}".format(base_balance),
                                           "{:.2f}".format(100 * bp),
                                           "{:.2f}".format(100 * recw),
                                           "{:.2f}".format(100 * difw)])
        self.ui.portfolio_data.append(['ALL', self.exchange.exchange_name, '-',
                                       "{:.2f}".format(self.portfolio_base_amount), '-', '-', '-', ])

    # endregion

    # region Price change data
    def _update_pctchange_data(self) -> None:
        self.ui.pctchange_data.clear()
        self.ui.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%']]
        for m in self.portfolio_base_markets:
            p = self.portfolio_ohlcv[m][-1][4]
            self.ui.pctchange_data.append([m, 'binance',
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-2][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-4][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-13][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-25][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-73][4])/p)])
    # endregion

    # region Portfolio quotes processor
    def _compare_weights(self, current: dict, recommended: dict):
        """Compare 2 dicts with same keys.
        Check keys before processing.

        :param current:
        :param recommended:
        :return:
        """
        if current is None or recommended is None:
            self.logger.warning('Nones')
            return False

        if (not isinstance(current, dict)) or (not isinstance(recommended, dict)):
            self.logger.warning('Not dict')
            return False

        shared_keys = set(current.keys()) & set(recommended.keys())

        if not (len(shared_keys) == len(current.keys()) and len(shared_keys) == len(recommended.keys())):
            self.logger.warning('Not all keys are shared')
            return False

        if isinstance(self.portfolio_difference, dict):
            self.portfolio_difference.clear()

        self.portfolio_difference = {x: rounded_to_precision(y - current[x], 4) for x, y in recommended.items()}

    def _generate_quotes(self):
        """
        Method for quote generation from provided tickers, recommended portfolio difference and
        current balances.
        Fill quote_collector with necessary quotes.
        """
        # Check for all_tickers and fetch if they are empty
        if not(isinstance(self.exchange.all_tickers, dict)):
            self.logger.info('Exchange tickers are empty, fetching...')
            self.exchange.process_tickers()
            t = self.exchange.all_tickers.copy()
        else:
            t = self.exchange.all_tickers.copy()
        if not(isinstance(self.portfolio_difference, dict)):
            self.logger.info("Portfolio difference dict are empty")
            return False
        elif not(len(self.portfolio_difference) > 0):
            self.logger.info("Portfolio difference dict are empty")
            return False
        else:
            d = self.portfolio_difference
        if not(isinstance(self.exchange.balances, dict)):
            self.logger.info('Balances are empty, fetching...')
            self.exchange.fetch_balances()
            b = self.exchange.balances
        else:
            b = self.exchange.balances
        for i in self.portfolio_difference.keys():
            if i not in b.keys():
                b[i] = {'free': 0, "locked": 0, "all": 0}
                # self.logger.info("No balance for some assets!")
                # return False
        # Define cross markets to avoid extra commission on rebalancing
        pcmall = ["{}/{}".format(x, y) for x in d for y in d]
        pcmall_s = [x for x in pcmall if x in t.keys()]
        # Filter for rebalancing_precision
        rw_pos = {}
        rw_neg = {}
        pos_cumsum = 0
        neg_cumsum = 0
        # Create dict with portfolio_base_amount and filter zero weights
        for a, w in d.items():
            if abs(w) >= self.rebalancing_precision:
                _ = {'rebal_target': w,
                     'free': b[a]['free'],
                     'locked': b[a]['locked'],
                     'all': b[a]['all'],
                     'base_amount': w * self.portfolio_base_amount}
                if w > 0:
                    rw_pos[a] = _
                    pos_cumsum += abs(w)
                elif w < 0:
                    rw_neg[a] = _
                    neg_cumsum += abs(w)
        # Iterate by positive weights and match with negative weights assets
        # Define amount to trade founding min of base_amount
        # Convert base amount to proper amount for symbol
        # Define price and other orders params
        # !!!Avoid refactoring before implementing non base assets!!!
        for a, b in rw_pos.items():
            for c, d in rw_neg.items():
                if "{}/{}".format(a, c) in pcmall_s:
                    symbol = "{}/{}".format(a, c)
                    base_amount = min(abs(b['base_amount']), abs(d['base_amount']))
                    # TODO Implement crossing spread behaviour
                    price = t[symbol]['bid']
                    amount = rounded_to_precision(self._count_symbol_amount(a, base_amount), 8)
                    # Avoid small amount quotes
                    if amount < 1e-6:
                        break
                    side = 'BUY'
                    order_type = 'LIMIT'
                    self.quote_collector.append({'symbol': symbol, 'order_type': order_type, 'side': side,
                                                 'amount': amount, 'price': price})
                    rw_neg[c]['base_amount'] += base_amount
                    rw_pos[a]['base_amount'] -= base_amount
                elif "{}/{}".format(c, a) in pcmall_s:
                    symbol = "{}/{}".format(c, a)
                    base_amount = min(abs(b['base_amount']), abs(d['base_amount']))
                    price = t[symbol]['ask']
                    amount = rounded_to_precision(self._count_symbol_amount(c, base_amount), 8)
                    # Avoid small amount quotes
                    if amount < 1e-6:
                        break
                    side = 'SELL'
                    order_type = 'LIMIT'
                    self.quote_collector.append({'symbol': symbol, 'order_type': order_type, 'side': side,
                                                 'amount': amount, 'price': price})
                    rw_neg[c]['base_amount'] += base_amount
                    rw_pos[a]['base_amount'] -= base_amount
                else:
                    self.logger.error("No market for trading assets")
        # Check for empty recommendations lists
        rw_pos.update(rw_neg)
        for x, y in rw_pos.items():
            if abs(y['base_amount']) > 10:
                self.logger.error('Not all recommendations filled')

    def _proceed_orders(self):
        """
        Print quotes from quote_collector.
        Check for dry_run option and place all orders from quote collector.
        Clear quote_collector and print order_history from an exchange class
        """
        if isinstance(self.quote_collector, list):
            if len(self.quote_collector) > 0:
                quotes_info = ["{} {} {}@{} placing...".format(x['side'], x['symbol'],
                                                               x['amount'], x['price']) for x
                               in self.quote_collector]
                self.ui.reload_ui(screen_data=quotes_info)
                # Define testing behaviour
                self.exchange.dry_run = self.dry_run
                # Place orders from quote_collector
                self.exchange.place_multiple_orders(self.quote_collector)
                # Clear quote_collector
                self.quote_collector.clear()
                # Parse exchange order history
                quotes_history_info = list()
                for x, y in self.exchange.order_history.items():
                    if y['status'] is not None:
                        quotes_history_info.append("{} {} {}@{} {} {} {}".format(
                                y['side'], y['symbol'], y['amount'], y['price'],
                                y['status'], y['client_order_id'], y['id']))
                self.ui.reload_ui(screen_data=quotes_history_info)
        else:
            self.ui.reload_ui(screen_data='Missing quote_collector')
    # endregion

    def _wait_timeout(self):
        """
        Check if reload timeout passed, use loop_interval from settings
        Use random generator and random seed equal time

        :return : True if timeout passed, False otherwise
        :rtype: bool
        """
        now_time = int(time()-1)
        seed(now_time)
        if (now_time - self.last_fetch_time > (randrange(*self.loop_interval))) or self.run_step == 0:
            self.last_fetch_time = now_time
            return True
        else:
            return False

    # region Main Loop
    def run_balancer(self):
        while True:
            sleep(1)
            for t in self.data_provider_list:
                if t == 'binance' and self._wait_timeout():
                    # Cancel non filled orders if exist
                    self.ui.reload_ui(statusbar_str="Fetching orders")
                    self.exchange.fetch_processed_orders()
                    self.ui.reload_ui(statusbar_str="Canceling orders")
                    self.exchange.cancel_processed_orders()
                    quotes_info = [x for x in self.quote_collector]
                    self.ui.reload_ui(statusbar_str="Load tickers", screen_data=quotes_info)
                    # Perform checking connections and previous lag
                    # self.exchange.sanity_check()
                    # Load and preprocess last tickers price
                    self.exchange.process_tickers()
                    # Fill ohlcv data
                    self.ui.reload_ui(statusbar_str="Load ohlcv")
                    self.portfolio_ohlcv.clear()
                    for _ in self.portfolio_base_markets:
                        self.portfolio_ohlcv[_] = self.exchange.get_ohlcv(_, timeframe='1h', limit=200)
                    # Fill balances data
                    self.ui.reload_ui(statusbar_str="Load balances")
                    self.exchange.fetch_balances()
                    self.balances = {x: y for x, y in self.exchange.balances.items() if x in self.portfolio_assets}
                    self._count_portfolio_base_amount()
                    self._update_portfolio_current_weights()
                    # Add data to lists for ui
                    self._update_index_data()
                    self._update_pctchange_data()
                    self._update_portfolio_data()
                    # Calculate optimize portfolio
                    self.ui.reload_ui(statusbar_str="Optimize portfolio")
                    d_frequency = 200
                    # Get recommended weights from optimizer
                    self.portfolio_recommended_weights, p_list = PortfolioOpt().generate_report(
                            pricing_data=self.portfolio_ohlcv,
                            weight_bounds=self.portfolio_weight_bounds,
                            base_asset=self.portfolio_base_asset,
                            frequency=d_frequency,
                            target_return=self.portfolio_target_return,
                            target_risk=self.portfolio_target_risk)
                    self.ui.reload_ui(portfolio_opt_data=p_list)
                    # Compare current and recommended weights
                    self._compare_weights(self.portfolio_current_weights, self.portfolio_recommended_weights)
                    # Reload ui with new recommendations data
                    self._update_portfolio_data()
                    # Add settings and portfolio recommendations data screen
                    self.ui.reload_ui(portfolio_opt_data=p_list)
                    # Generate quotes and fill quote_collector
                    self.ui.reload_ui(statusbar_str="Generate quotes")
                    self._generate_quotes()
                    quotes_info = ["{} {} {}@{}".format(x['side'], x['symbol'],
                                                        x['amount'], x['price']) for x in self.quote_collector]
                    self.ui.reload_ui(screen_data=quotes_info)

                if t == 'kucoin':
                    pass

            # # Check if quote_collector not empty
            # # Proceed trades
            # if len(self.quote_collector) == 0:
            #     self.logger.info("Quote collector is empty. Ready to generate provided quotes")
            # else:
            # # Generate quotes
            #     self._generate_quotes()
            # Place an orders and clear quote collector on return
            if len(self.quote_collector) != 0:
                self.ui.reload_ui(statusbar_str="Proceed orders")
                self._proceed_orders()

            if self.file_watcher.look():
                # Re init Runner with new settings
                self.ui.reload_ui(statusbar_str="Reinit runner with new settings")
                self.__init__(logger=self.logger,
                              watcher=self.file_watcher,
                              **self.file_watcher.settings)
            self.run_step += 1
            self.ui.reload_ui(statusbar_str="OK")
            # Wait for sleep timeout
            # sleep(1)
            # if (self.run_step % write_interval == 0) and (self.run_step != 0):
            #     self.exchange.tob_to_pickle(self.cache_path)

    # endregion
