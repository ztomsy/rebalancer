#!/usr/bin/env python
# encoding: utf-8

from time import sleep, time_ns, time
from sys import exit
from random import randrange

from binance.restclient import RestClient
from payload.trader import Trader
from core.ui_curses import UI_curses, curses
from core.influx import Influx
from core.core import rounded_to_precision


class Runner(object):
    """
    Init and run main loop
    """

    def __init__(self, logger: object = None,  **kwargs):
        """
        Init counter and enable logging
        """
        self.logger = logger
        self.last_fetch_time = int(time())
        self.dry_run = kwargs['DRY_RUN']
        # Init screen with ui
        self.ui = UI_curses()
        self.ui.print_ui()
        # Init database connection
        self.influx = Influx(kwargs['INFLUX_DATA'])
        # Init index values
        self.scindex = kwargs['SCINDEX']
        self.scindex_markets = None
        self.scindex_tickers = None
        # Init portfolio
        self.portfolio = kwargs['PORTFOLIO']
        self.portfolio_base_asset = kwargs['PORTFOLIO_BASE_ASSET']
        self.portfolio_base_volume: float = 0
        self.portfolio_assets = [x for x in self.portfolio.keys()]

        self.run_step = 0
        self.balances = []

        # Initialise exchanges
        self.data_provider_list = []
        self.exchange1 = RestClient(window=kwargs['AUTH_DATA']['binance']['window'],
                                    api_key=kwargs['AUTH_DATA']['binance']['api_key'],
                                    secret=kwargs['AUTH_DATA']['binance']['secret'],
                                    verbose=False,
                                    logger=logger)
        # TODO Add data provider list
        self.data_provider_list.append('binance')
        # self.data_provider_list.append(['binance', self.exchange1])
        # Load index markets
        self.scindex_markets = [x for x, y in self.exchange1.markets.items() if (y['base'] in self.scindex and y[
            'quote'] == 'BTC') or (y['quote'] in self.scindex and y['base'] == 'BTC')]
        # Get all tickers
        self.exchange1.get_all_tickers()
        # Sort only open markets
        self.scindex_tickers = {x for x in self.scindex_markets if self.exchange1.all_tickers[x]['askVolume'] > 0 and
                                self.exchange1.all_tickers[x]['askVolume'] > 0}
        # After filtering tickers, combine new index markets
        self.scindex_markets = [x for x in self.scindex_markets if x in
                                self.scindex_tickers]
        self.exchange1.calc_tickers(self.scindex_markets)
        # Get portfolio markets
        # TODO Unify to use assets which dont have a USDT markets as other base asssets option
        self.portfolio_markets = [x for x, y in self.exchange1.markets.items() if (y['base'] in self.portfolio_assets
                                                                                   and y['quote'] ==
                                                                                   self.portfolio_base_asset) or (y['quote'] in self.portfolio_assets
                                                                                   and y['base'] ==
                                                                                   self.portfolio_base_asset)]
        self.exchange1.calc_tickers(self.portfolio_markets)
        # Quote collector container
        self.quote_collector = []

        # Run main loop and close threads on exit
        try:
            self.run_balancer()
        finally:
            try:
                curses.endwin()
                self.logger.info("Closing curses")
            finally:
                pass
            self.logger.info("Shutdown application")
            # self.exchange2.execute.shutdown()
            # self.exchange1.order_history_to_pickle(self.cache_path)

    # region Index data
    def _update_index_data(self):
        self.ui.index_data.clear()
        self.ui.index_data = [['NAME', 'PROVIDER', 'TOB ASK', 'TOB BID', 'MID', 'SPREAD', 'SPREAD%'], ]
        for s in self.scindex_markets:
            ticker = self.exchange1.all_tickers[s]
            self.ui.index_data.append([s, 'binance',
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
        for m in self.portfolio_markets:
            if asset in m:
                if 'BTC' in m:
                    if asset == 'USDT':
                        return amount/self.portfolio_ohlcv[m][-1][4]
                    else:
                        return amount*self.portfolio_ohlcv[m][-1][4]

    def _count_base_balance(self, asset):
        if asset == self.portfolio_base_asset:
            base_balance = self.balances[asset]['all']
        elif asset == 'USDT':
            base_balance = self.balances[asset]['all'] / self.portfolio_ohlcv[
                "{}/{}".format(self.portfolio_base_asset, asset)][-1][4]
        else:
            base_balance = self.balances[asset]['all'] * self.portfolio_ohlcv[
                "{}/{}".format(asset, self.portfolio_base_asset)][-1][4]
        return base_balance

    def _update_portfolio_data(self):
        self.ui.portfolio_data.clear()
        self.ui.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'BASEPRICE', 'MIN%', 'CURRENT%', 'MAX%'],]
        pbv = 0
        for c in self.portfolio_assets:
            pbv += self._count_base_balance(c)
        for c in self.portfolio_assets:
            base_balance = float(self._count_base_balance(c))
            self.ui.portfolio_data.append([c, 'binance', "{:.4f}".format(self.balances[c]['all']),
                                        "{:.2f}".format(base_balance),
                                        "{:.2f}".format(self.portfolio[c]['min']),
                                        "{:.2f}".format(100*base_balance/pbv),
                                        "{:.2f}".format(self.portfolio[c]['max'])])
        self.portfolio_base_volume = pbv
        self.ui.portfolio_data.append(['ALL', 'binance', '-',
                                    "{:.2f}".format(pbv), '-', '-', '-', ])
    # endregion

    # region Price change data
    def _update_pctchange_data(self) -> None:
        self.ui.pctchange_data.clear()
        self.ui.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%']]
        for m in self.portfolio_markets:
            p = self.portfolio_ohlcv[m][-1][4]
            self.ui.pctchange_data.append([m, 'binance',
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-2][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-4][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-13][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-25][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-73][4])/p)])
    # endregion

    def _calculate_portfolio_recommendations(self):
        pass

    def _generate_quotes(self):
        pass

    def _wait_timeout(self):
        now_time = int(time()-1)
        if (now_time - self.last_fetch_time > (randrange(40, 60))) or self.run_step == 0:
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
                    self.ui.reload_ui(statusbar_str="Last update: {:>2}s | Status: Loading tickers | ".format(
                            int(self.last_fetch_time - time())))
                    # self.exchange1.sanity_check() # Perform checking connections and previous lag
                    # Load last tickers prices
                    self.exchange1.get_all_tickers()
                    # And calculate some routines for tickers
                    self.exchange1.calc_tickers(self.scindex_markets)
                    # Add index data to list
                    self._update_index_data()
                    # Fill ohlcv data
                    self.ui.reload_ui(statusbar_str="Last update: {:>2}s | Status: Loading ohlcv | ".format(
                            int(self.last_fetch_time - time())))
                    self.portfolio_ohlcv = {}
                    for _ in self.portfolio_markets:
                        self.portfolio_ohlcv[_] = self.exchange1.get_ohlcv(_, timeframe='1h')
                    # Fill balances data
                    self.ui.reload_ui(statusbar_str="Last update: {:>2}s | Status: Loading balances | ".format(
                            int(self.last_fetch_time - time())))
                    self.exchange1.fetch_balances()
                    self.balances = {x: y for x, y in self.exchange1.balances.items() if x in self.portfolio_assets}
                    # Calculate portfolio recommendations
                    self._calculate_portfolio_recommendations()
                    # Add data to lists
                    self._update_pctchange_data()
                    # Fill portfolio data

                    # Add data to lists
                    self._update_portfolio_data()

                if t == 'kucoin':
                    pass
                if t == 'twim':
                    pass

            # # Check if quote_collector not empty
            # # Proceed trades
            # if len(self.quote_collector) == 0:
            #     self.logger.info("Quote collector is empty. Ready to generate provided quotes")
            # else:
            # # Generate quotes
            #     self._generate_quotes()
            # # Place an orders and clear quote collector on return
            # if self.exchange1.place_orders(self.quote_collector):
            #     self.quote_collector = []
            # else:
            #     self.logger.error("While placing orders we catch an error:", exc_info=True)
            #     exit(56)
            self.ui.reload_ui(statusbar_str="Last update: {:>2}s | Status: OK | ".format(
                    int(time() - self.last_fetch_time)))
            # self.ui.push_data("Last update: {:>2}s | Status: OK | ".format(
            #         int(time() - self.last_fetch_time)))
            # self.ui.print_ui()
            self.run_step += 1
            # Wait for next input
            # self.ui.key_pressed = self.ui.stdscr.getch()

            # if (self.run_step % write_interval == 0) and (self.run_step != 0):
            #     self.exchange1.tob_to_pickle(self.cache_path)

    # endregion
