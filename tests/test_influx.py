from unittest import TestCase
from yat.influx import Influx
import settings

order1 = {'id': '441793725', 'timestamp': 1560791405253,
          'datetime': '2019-06-17T17:10:05.253Z', 'lastTradeTimestamp': None,
          'symbol': 'BTC/USDT', 'type': 'limit',
          'side': 'buy', 'price': 9220.49, 'amount': 0.001,
          'cost': 0.00001, 'average': None,
          'filled': 0.001, 'remaining': 0.0,
          'status': 'closed', 'fee': 0.00001, 'trades': None,
          'client_order_id': '502521563'}


class TestInflux(TestCase):
    def setUp(self) -> None:
        self.tr = Influx# (settings.INFLUX_DATA)

    def test__write_points(self):
        pass

    def test__query(self):
        pass

    def test_report_order(self):
        Influx.report_order(self.tr, order1, 'test_provider', 'test_exchange')

    def test_report_market_state(self):
        pass
