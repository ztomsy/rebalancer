from math import log
from statistics import pstdev
import numpy as np
from numpy import mean

class Signal:
    '''
    Class to store, update and manipulate the signal
    '''

    def __init__(self, window: int = 30, valpha: float = 0.25):
        '''
        Initialize signal constructor with a set of lists and dicts and other defaults.
        Lists are preconstructed on init to avoid IndexError.
        _bask_price, _bask_quantity, bbid_price, bbid_quantity are best ask and bid price
        and quantity lists respectively, quantities are preload with min precision.
        askmacd and bidmacd are lists of previous macd signal states
        mid, midl1 are current and previous midle price(bask + bbid)/2
        ret10 are list filled with log variance of mid price used to calc pstdev on it
        askov, bidov are ZigZag strategy description, see "Regime Switching and Technical
        Trading with Dynamic Bayesian Networks in High-Frequency Stock Markets"
        https://uwspace.uwaterloo.ca/handle/10012/4463
        '''

        self._window = window
        self._bask_price = [0] * window
        self._bask_quantity = [0.001] * window  # Fill quantity window with min precision
        self._bbid_price = [0] * window
        self._bbid_quantity = [0.001] * window   # Fill quantity window with min precision
        # Dicts contain
        self.askmacd = [0] * window
        self.bidmacd = [0] * window
        # Mid price
        self.mid = 0
        self.midl1 = 0
        self.ret10 = [0] * 10
        # ZigZag Strategy
        self._valpha = valpha
        self.askov = [0] * 3
        self.bidov = [0] * 3
        # MACD Strategy
        self.askmacds = [0] * 2
        self.bidmacds = [0] * 2


    def make_mid_signal(self, step, bid, ask):
        self.mid = (ask + bid) / 2
        if self.midl1 == 0:
            self.midl1 = self.mid
        self.ret10[step % 10] = 100 * log(self.mid / self.midl1)
        self.midl1 = self.mid

    def make_vol_signal(self):
        return pstdev(self.ret10)

    def reset_current(self):
        self.oibv = 0
        self.arrv = 0

    def makeov_signal(self, step: int):
        '''
        Calculate corresponding feature set for top ask and bid statements
        f0 represents the direction of zig-zag leg, while we count exact momentum for analyze we get
        sign of it result
        f1 indicates a trend
        f2 is an average volume variation
        :param step: Current step id
        :return: None
        '''
        # f0 as momentum describe
        askmmts = self._bask_price[-1] - self._bask_price[-2]
        askf0 = -1 if askmmts < 0 else 1 if askmmts > 0 else 0

        bidmmts = self._bbid_price[-1] - self._bbid_price[-2]
        bidf0 = -1 if bidmmts < 0 else 1 if bidmmts > 0 else 0

        # f1 as trend watcher
        if ((self._bask_price[-5] < self._bask_price[-3] < self._bask_price[-1])
                and (self._bask_price[-4] < self._bask_price[-2])):
            askf1 = 1
        elif ((self._bask_price[-5] > self._bask_price[-3] > self._bask_price[-1])
              and (self._bask_price[-4] > self._bask_price[-2])):
            askf1 = -1
        else:
            askf1 = 0

        if ((self._bbid_price[-5] < self._bbid_price[-3] < self._bbid_price[-1])
                and (self._bbid_price[-4] < self._bbid_price[-2])):
            bidf1 = 1
        elif ((self._bbid_price[-5] > self._bbid_price[-3] > self._bbid_price[-1])
              and (self._bbid_price[-4] > self._bbid_price[-2])):
            bidf1 = -1
        else:
            bidf1 = 0

        # To define f2 we first define some intermediary variables
        v1n = self._bask_quantity[-1] / self._bask_quantity[-2]
        v2n = self._bask_quantity[-1] / self._bask_quantity[-3]
        v3n = self._bask_quantity[-2] / self._bask_quantity[-3]

        vt1n = 1 if (v1n - 1) > self._valpha else -1 if (1 - v1n) > self._valpha else 0
        vt2n = 1 if (v2n - 1) > self._valpha else -1 if (1 - v2n) > self._valpha else 0
        vt3n = 1 if (v3n - 1) > self._valpha else -1 if (1 - v3n) > self._valpha else 0

        askf2 = 1 if vt1n == 1 and vt2n > -1 and vt3n < 1 else -1 if vt1n == -1 and vt2n < 1 and vt3n > -1 else 0

        v1n = self._bbid_quantity[-1] / self._bbid_quantity[-2]
        v2n = self._bbid_quantity[-1] / self._bbid_quantity[-3]
        v3n = self._bbid_quantity[-2] / self._bbid_quantity[-3]

        vt1n = 1 if (v1n - 1) > self._valpha else -1 if (1 - v1n) > self._valpha else 0
        vt2n = 1 if (v2n - 1) > self._valpha else -1 if (1 - v2n) > self._valpha else 0
        vt3n = 1 if (v3n - 1) > self._valpha else -1 if (1 - v3n) > self._valpha else 0

        bidf2 = 1 if vt1n == 1 and vt2n > -1 and vt3n < 1 else -1 if vt1n == -1 and vt2n < 1 and vt3n > -1 else 0

        # For ask we have ov as (askf0, askf1, askf2) vector
        self.askov = (askf0, askf1, askf2)
        self.bidov = (bidf0, bidf1, bidf2)

    def makemacd_signal(self, step: int) -> None:
        # Calculate last 10 and 20 elements mean difference as macd for longer trend
        N1 = len(self._bask_price) if len(self._bask_price) < 10 else 10
        askema10 = np.average(self._bask_price[-10:], weights=np.exp(np.linspace(-1, 0, N1)))
        bidema10 = np.average(self._bbid_price[-10:], weights=np.exp(np.linspace(-1, 0, N1)))

        N2 = len(self._bask_price) if len(self._bask_price) < 20 else 20
        askema20 = np.average(self._bask_price[-20:], weights=np.exp(np.linspace(-1, 0, N2)))
        bidema20 = np.average(self._bbid_price[-20:], weights=np.exp(np.linspace(-1, 0, N2)))

        askmacd = askema10 - askema20
        # f0 store trend direction
        askmacdf0 = -1 if askmacd < 0 else 1 if askmacd > 0 else 0
        lagedaskmacd = mean(self.askmacd)
        # f1 store exact amount as trend force
        askmacdf1 = askmacd - lagedaskmacd

        bidmacd = bidema10 - bidema20
        bidmacdf0 = -1 if bidmacd < 0 else 1 if bidmacd > 0 else 0
        lagedbidmacd = mean(self.bidmacd)
        bidmacdf1 = bidmacd - lagedbidmacd

        # MACD strategy vector as long trend detector
        self.askmacds = (askmacdf0, np.around(askmacdf1, 4))
        self.bidmacds = (bidmacdf0, np.around(bidmacdf1, 4))

        self.askmacd.append(askmacd)
        self.bidmacd.append(bidmacd)

        if len(self.askmacd) > self._window:
            del(self.askmacd[0])
            del(self.bidmacd[0])

    def make_signal(self, tob: dict, step: int):

        # Update best ask and bid lists
        self._bask_price.append(tob['bask_price'])
        self._bask_quantity.append(tob['bask_quantity'])
        self._bbid_price.append(tob['bbid_price'])
        self._bbid_quantity.append(tob['bbid_quantity'])

        if len(self._bask_price) > self._window:
            del(self._bask_price[0])
            del(self._bask_quantity[0])
            del(self._bbid_price[0])
            del(self._bbid_quantity[0])

        self.makeov_signal(step)
        self.makemacd_signal(step)
        self.make_mid_signal(step, tob['bbid_price'], tob['bask_price'])

        return {'run_step': step,
                'askov': self.askov,
                'bidov': self.bidov,
                'askmacds': self.askmacds,
                'bidmacds': self.bidmacds,
                # 'mid': self.mid,
                'vol': self.make_vol_signal()
                }
