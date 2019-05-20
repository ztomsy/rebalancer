#!/usr/bin/env python
# encoding: utf-8

from time import sleep, time_ns, time
from sys import exit
from random import randrange

from binance.restclient import RestClient
from payload.trader import Trader
from core.ui_curses import UI_curses, curses
from core.influx import Influx


class Runner(object):
    """
    Init and run main loop
    """

    def __init__(self, logger: object = None,  **kwargs):
        """
        Init counter and enable logging
        """
        self.logger = logger
        self.now_time = int(time())
        self.dry_run = kwargs['DRY_RUN']
        # Init screen with ui
        self.ui = UI_curses()
        self.ui.print_ui()
        sleep(1)
        # Init database connection
        self.influx = Influx(kwargs['INFLUX_DATA'])

        # Init screen api data containers
        self.header_str = ""
        self.statusbar_str = ""
        self.index_data = [['NAME', 'PROVIDER', 'VOLUME24', 'VDISTR', 'TOB ASK', 'TOB BID', 'SLP ASK', 'SLP BID'],
                           ['-', '-', 0, 0, 0, 0, 0, 0], ]
        self.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'SCIPRICE', 'MIN%', 'CURRENT%', 'MAX%', 'INFO'],
                          ['-', '-', 0, 0, 0, 0, 0, 0], ]
        self.pctchange_data = [['NAME', 'PROVIDER', 'BALANCE', 'SCIPRICE', 'TOB ASK', 'TOB BID', 'SLP ASK', 'SLP BID'],
                     ['-', '-', 0, 0, 0, 0, 0, 0], ]
        self.portfolio = kwargs['PORTFOLIO']
        self.portfolio_assets = [x for x in self.portfolio.keys()]
        self.portfolio_sci_volume: float = 0
        self.scindex = kwargs['SCINDEX']
        self.scindex_value = None

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
        self.scindex_tickers = {x: y for x, y in self.exchange1.all_tickers.items() if x in
                                self.scindex_markets and y['bidVolume'] > 0 and y['askVolume'] > 0}
        for x, y in self.scindex_tickers.items(): y['timestamp'] = time_ns()
        # After filtering tickers, combine new index markets
        self.scindex_markets = [x for x in self.scindex_markets if x in
                                self.scindex_tickers.keys()]
        # Get portfolio markets
        self.portfolio_markets = [x for x, y in self.exchange1.markets.items() if (y['base'] in self.portfolio_assets
                                                                                   and y['quote'] in self.portfolio_assets)]
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
    def _calculate_index(self):
        overall_volume = 0
        index_ask_price = 0
        index_bid_price = 0
        for s in self.scindex_markets:
            overall_volume += self.exchange1.all_tickers[s]['baseVolume']
        for s in self.scindex_markets:
            index_ask_price += self.exchange1.all_tickers[s]['ask']*self.exchange1.all_tickers[s][
                'baseVolume']/overall_volume
            index_bid_price += self.exchange1.all_tickers[s]['bid']*self.exchange1.all_tickers[s][
                'baseVolume']/overall_volume
        self.scindex_value = {'volume24': overall_volume, 'ask': index_ask_price, 'bid': index_bid_price}
        return overall_volume, index_ask_price, index_bid_price

    def _update_index_data(self):
        self.index_data.clear()
        self.index_data = [['NAME', 'PROVIDER', 'VOLUME24', 'VDISTR', 'TOB ASK', 'TOB BID', 'SLP ASK', 'SLP BID'],]
        o, ia, ib = self._calculate_index()
        self.index_data.append(['SCINDEX', 'binance', "{:.2f}".format(o), '-',
                                "{:.2f}".format(ia), "{:.2f}".format(ib),
                                "{:.2f}".format(ia), "{:.2f}".format(ib)])
        for s in self.scindex_markets:
            volume24 = self.exchange1.all_tickers[s]['baseVolume']
            tob_ask = self.exchange1.all_tickers[s]['ask']
            tob_bid = self.exchange1.all_tickers[s]['bid']
            self.index_data.append([s, 'binance', "{:.2f}".format(volume24), "{:.2f}".format(volume24/o),
                                    "{:.2f}".format(tob_ask), "{:.2f}".format(tob_bid),
                                    "{:.2f}".format(tob_ask), "{:.2f}".format(tob_bid)])
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

    def _count_sci_balance(self, asset):
        if asset == 'BTC':
            btc_balance = self.balances[asset]['all']
        else:
            btc_balance = self._count_btc_balance(self.balances[asset]['all'], asset)

        return btc_balance * (self.scindex_value['ask']+self.scindex_value['bid'])/2

    def _update_portfolio_data(self):
        self.portfolio_data.clear()
        self.portfolio_sci_volume = 0
        self.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'SCIPRICE', 'MIN%', 'CURRENT%', 'MAX%', 'INFO'],]
        for c in self.portfolio_assets:
            self.portfolio_sci_volume += self._count_sci_balance(c)
        sci_cum_balance = 0
        for c in self.portfolio_assets:
            sci_balance = self._count_sci_balance(c)
            sci_cum_balance += sci_balance
            self.portfolio_data.append([c, 'binance', "{:.4f}".format(self.balances[c]['all']),
                                        "{:.2f}".format(float(sci_balance)),
                                        "{:.2f}".format(self.portfolio[c]['min']),
                                        "{:.2f}".format(100*float(sci_balance)/self.portfolio_sci_volume),
                                        "{:.2f}".format(self.portfolio[c]['max']), "{:.2f}".format(0)])
        self.portfolio_data.append(['ALL', 'binance', '-',
                                    "{:.2f}".format(sci_cum_balance), '-', '-', '-', '-',])
    # endregion

    # region Price change data
    def _update_pctchange_data(self) -> None:
        self.pctchange_data.clear()
        self.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '6H%', '12H%', '24H%', '72H%']]
        for m in self.portfolio_markets:
            p = self.portfolio_ohlcv[m][-1][4]
            self.pctchange_data.append([m, 'binance',
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-2][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-4][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-7][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-13][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-25][4])/p),
                                        "{:+.2f}".format(100*(p-self.portfolio_ohlcv[m][-73][4])/p)])
    # endregion

    def _calculate_portfolio_recommendations(self):
        pass

    def _generate_quotes(self):
        pass

    def _wait_timeout(self):
        now_time = int(time())
        if (now_time - self.now_time > (30+randrange(10, 30))) or self.run_step == 0:
            self.now_time = now_time
            return True
        else:
            return False

    # region Main Loop
    def run_balancer(self):
        while True:
            sleep(1)
            for t in self.data_provider_list:
                if t == 'binance' and self._wait_timeout():
                    self.ui.push_data("Rebalancer",
                                      "Last update: {}s | Status: Loading | ".format(int(self.now_time-time())),
                                      self.index_data, self.portfolio_data, self.pctchange_data)
                    self.ui.print_ui()
                    # self.exchange1.sanity_check() # Perform checking connections and previous lag
                    # Clear tickers data
                    self.exchange1.all_tickers = {}
                    # Fill index data
                    for symbol in self.scindex_markets:
                        self.exchange1._fetch_ticker(symbol)
                    # Add index data to list
                    self._update_index_data()
                    # Fill ohlcv data
                    self.portfolio_ohlcv = {}
                    for symbol in self.portfolio_markets:
                        self.portfolio_ohlcv[symbol] = self.exchange1.get_ohlcv(symbol, timeframe='1h')
                    # Calculate portfolio recommendations
                    self._calculate_portfolio_recommendations()
                    # Add data to lists
                    self._update_pctchange_data()
                    # Fill portfolio data
                    self.exchange1.fetch_balances()
                    self.balances = {x: y for x, y in self.exchange1.balances.items() if x in self.portfolio_assets}
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
            self.ui.push_data('Rebalancer',
                              "Last update: {}s | Status: OK | ".format(int(self.now_time-time())),
                              self.index_data, self.portfolio_data, self.pctchange_data)
            self.ui.print_ui()
            self.run_step += 1
            # Wait for next input
            # self.ui.key_pressed = self.ui.stdscr.getch()

            # if (self.run_step % write_interval == 0) and (self.run_step != 0):
            #     self.exchange1.tob_to_pickle(self.cache_path)

    # endregion
