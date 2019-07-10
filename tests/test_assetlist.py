# pragma pylint: disable=missing-docstring,C0103,protected-access

from unittest.mock import MagicMock, PropertyMock
import unittest

from yat.assetlist import AssetList, StaticAssetList
from yat import logger
from logging import DEBUG

class TestExchange:
    markets = {'AE/BTC': {'base':'AE', 'quote':'BTC'},
               'ETH/USDT': {'base':'ETH', 'quote':'USDT'},
               'BTC/USDT': {'base':'BTC', 'quote':'USDT'},
               'BNB/USDT': {'base':'BNB', 'quote':'USDT'},
               'XXX/ZZZ': {'base':'XXX', 'quote':'ZZZ'}, }


p_b_asset = 'USDT'
white_list = ['BTC',
              'ETH',
              'BNB',
              'USDT',
              # 'USDSB',
              'AE', ]
black_list = ['USDSB', ]
weight_bounds = (0.05, 0.95)

# Init logger and define log_level verbosity
logger = logger.setup_custom_logger('Tests', log_level=DEBUG)


class TestStaticAssetList(unittest.TestCase):

    def setUp(self) -> None:
        self.al = StaticAssetList.StaticAssetList(logger,
                                                  TestExchange,
                                                  white_list,
                                                  black_list,
                                                  weight_bounds)


class Test_build_portfolio_assets_markets(TestStaticAssetList):
    def test_build_portfolio_assets_markets(self):
        p_b_markets = self.al.build_portfolio_assets_markets('USDT')
        self.assertEqual(len(p_b_markets), 4)
        self.assertEqual(len(self.al.whitelist), 5)
        self.assertListEqual(['USDSB'], self.al.blacklist)
        self.assertDictEqual({'USDT': (0.05, 0.95),
                              'ETH': (0.05, 0.95),
                              'BTC': (0.05, 0.95),
                              'BNB': (0.05, 0.95),
                              'AE': (0.05, 0.95)},
                             self.al.portfolio)


class Test_refresh_assetlist(TestStaticAssetList):
    def test_refresh_assetlist(self):
        self.al.refresh_assetlist()
        self.assertEqual(len(self.al.whitelist), 2)

