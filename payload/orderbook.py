#!/usr/bin/env python
# encoding: utf-8
import time
import numpy as np

from payload.obSignal import ObSignal


class Orderbook:

    def __init__(self, window: int = 100, logger: object = None):
        """
        Initialize the Orderbook with a set of empty dicts and other defaults
        Create local instance of ObSignal class to track orderbooks states
        _bid_book and _ask_book: sorted list of presented order book state
        _tob are list of dicts with tob data indexed by add order
        _lob are list of order book tuples (run_step, ask_book, bid_book) indexed by add order
        """
        self.logger = logger

        self.Signal = ObSignal()

        self._ask_book = list()
        self._bid_book = list()
        # window also affect _tob, _lob lists length
        self._window = window
        self._tob = list()
        self._lob = list((0, self._ask_book, self._bid_book))
        # Save spread states as best_ask_price - best_bid_price on current ex
        self._spreads = [0]

        self._signal = list()  # only list last gen list

    def update_ob(self, order_book: dict, run_step: int, spread_lag_size: int):
        '''
        Wrap ob from ccxt into our ob class and call signal and tob update
        :param order_book: pure ccxt orderbook dict
        :param run_step: step number
        :param spread_lag_size: lag_size param for spread counting in _update_tob
        '''
        self._ask_book.clear()
        self._bid_book.clear()

        self._ask_book = order_book['asks']
        self._bid_book = order_book['bids']

        self._update_tob(run_step, spread_lag_size)
        self._update_lob(run_step, spread_lag_size)
        self._update_signal(run_step)

    def _update_signal(self, run_step: int) -> None:
        """
        Append signal list and remove last value if len is more then window
        :param run_step:
        :return: None
        """
        if len(self._signal) > self._window:
            del (self._signal[0])
        self._signal.append(self.Signal.make_signal(self.report_top_of_book(), run_step))

    def _update_lob(self, run_step: int, spread_lag_size: int) -> None:
        # self._lob.append(list(run_step, list(self._ask_book), list(self._bid_book)))
        pass

    def _update_tob(self, run_step: int, spread_lag_size: int) -> None:
        """
        Append top of book list and remove last value if len is more then window.
        We check for positive spread there to avoid simple errors with name wrapping.
        Simple MM algorithms does not use previous tob states so we can store only last statement.
        :param run_step: step number
        :param spread_lag_size: lag_size param for spread counting in _update_tob
        :return: None
        """
        if len(self._spreads) > self._window:
            del (self._spreads[0])
            del (self._tob[0])
        # Update spread data
        self._spreads.append(self._ask_book[0][0] - self._bid_book[0][0])
        # we check again for positive spread to avoid problem with name wrapping
        try:
            self._spreads[-1] >= 0 is True
        except:
            self.logger.exception("Spread is negative, check you data consistency!", exc_info=True)
            # sys.exit(65)  # 65 data format error
        #  Calculate mean spread on window
        lagged_mean_spread = np.mean(self._spreads[spread_lag_size:])
        # Prepare dict for update
        tobd = {'run_step':      run_step,
                'timestamp':     time.time_ns(),  # nanoseconds precision
                'bask_price':    self._ask_book[0][0],
                'bask_quantity': self._ask_book[0][1],
                'bbid_price':    self._bid_book[0][0],
                'bbid_quantity': self._bid_book[0][1],
                'mid_price':     (self._ask_book[0][0] + self._bid_book[0][0]) / 2,
                'spread':        self._ask_book[0][0] - self._bid_book[0][0],
                'lag_spread':    lagged_mean_spread}
        self._tob.append(tobd)

    def report_top_of_book(self, step: int = -1):
        """
        Report latest top of book if step is not provided,
        otherwise return tob of required step.
        _tob list is ordered by injection and latest tob
        have to be with the same index as global run_step parameter
        :return: Dict with latest tob
        """
        return self._tob[step]
