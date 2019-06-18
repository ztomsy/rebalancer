import unittest
from payload.portfolioOpt import PortfolioOpt

pricing_data_2 = {
    'BTC/USDT': [[1559034000000, 8710.74, 8743.85, 8692.54, 8711.43, 1052.468837],
                 [1559037600000, 8712.89, 8718.8, 8647.1, 8683.12, 1318.354504],
                 [1559041200000, 8683.12, 8743.0, 8668.8, 8734.36, 1081.65452]],
    'ETH/USDT': [[1559034000000, 270.11, 271.0, 269.01, 270.23, 14036.69663],
                 [1559037600000, 270.23, 270.49, 267.75, 268.75, 15579.44674],
                 [1559041200000, 268.75, 271.0, 267.75, 270.31, 15008.81771]],
    'BNB/USDT': [[1559034000000, 33.4477, 33.4798, 33.0909, 33.191, 135370.75],
                 [1559037600000, 33.1813, 33.4977, 33.0205, 33.2011, 156239.12],
                 [1559041200000, 33.1784, 33.4717, 33.112, 33.4503, 201280.92]]
}

pricing_data = {'BNB/BTC':  [[1559818800000, 0.0040599, 0.0040803, 0.0040448, 0.0040715, 118153.28],
                             [1559822400000, 0.0040715, 0.004073, 0.0040216, 0.0040239, 122524.7],
                             [1559826000000, 0.0040259, 0.0040424, 0.0040056, 0.0040206, 108059.99],
                             [1559829600000, 0.00402, 0.0040207, 0.003972, 0.0039936, 68399.02],
                             [1559833200000, 0.003991, 0.0040165, 0.0039879, 0.0040117, 10286.37]],
                'BNB/ETH':  [[1559818800000, 0.129004, 0.129649, 0.128541, 0.129576, 2192.35],
                             [1559822400000, 0.129576, 0.129683, 0.127687, 0.127795, 3863.44],
                             [1559826000000, 0.127917, 0.128341, 0.126857, 0.127539, 2752.44],
                             [1559829600000, 0.127539, 0.127539, 0.1253, 0.126206, 6426.06],
                             [1559833200000, 0.126204, 0.1271, 0.126204, 0.1271, 672.44]],
                'BNB/USDT': [[1559818800000, 31.6015, 31.929, 31.5787, 31.8971, 161252.27],
                             [1559822400000, 31.8844, 31.96, 31.0348, 31.1578, 226336.86],
                             [1559826000000, 31.1718, 31.1841, 30.61, 31.002, 142418.47],
                             [1559829600000, 31.002, 31.025, 30.1928, 30.6608, 107857.95],
                             [1559833200000, 30.6607, 30.8888, 30.5505, 30.8885, 9763.01]],
                'XRP/BNB':  [[1559818800000, 0.01267, 0.0127, 0.01261, 0.01262, 123062.7],
                             [1559822400000, 0.01261, 0.01276, 0.01261, 0.01276, 244539.8],
                             [1559826000000, 0.01273, 0.01283, 0.01272, 0.01278, 196468.0],
                             [1559829600000, 0.01278, 0.01295, 0.01278, 0.01288, 364455.2],
                             [1559833200000, 0.01289, 0.0129, 0.01279, 0.01279, 117197.7]],
                'BNB/PAX':  [[1559818800000, 31.7161, 31.9433, 31.6743, 31.9433, 400.68],
                             [1559822400000, 31.9815, 32.0173, 31.2357, 31.2357, 1438.25],
                             [1559826000000, 31.18, 31.3032, 30.7373, 31.1299, 1997.59],
                             [1559829600000, 31.062, 31.062, 30.2501, 30.5664, 1234.44],
                             [1559833200000, 30.7304, 30.9028, 30.7304, 30.9028, 97.6]],
                'BNB/TUSD': [[1559818800000, 31.6193, 31.8686, 31.6193, 31.8686, 546.22],
                             [1559822400000, 31.8848, 31.9961, 31.2338, 31.2338, 3064.51],
                             [1559826000000, 31.1869, 31.2718, 30.7301, 31.0797, 2152.86],
                             [1559829600000, 31.0125, 31.0125, 30.2172, 30.5946, 4628.44],
                             [1559833200000, 30.7374, 30.9289, 30.618, 30.9289, 60.75]],
                'BNB/USDC': [[1559818800000, 31.6282, 31.9456, 31.6279, 31.9456, 1433.61],
                             [1559822400000, 31.965, 31.9987, 31.1992, 31.2471, 1890.94],
                             [1559826000000, 31.1885, 31.2853, 30.7194, 31.0884, 2148.78],
                             [1559829600000, 31.0025, 31.0025, 30.2001, 30.7122, 3028.0],
                             [1559833200000, 30.6564, 30.9346, 30.6292, 30.9346, 320.28]],
                'BNB/USDS': [[1559818800000, 31.5369, 31.5369, 31.5369, 31.5369, 0.0],
                             [1559822400000, 31.5236, 31.5236, 31.413, 31.4133, 20.95],
                             [1559826000000, 31.14, 31.3199, 31.0924, 31.1282, 57.5],
                             [1559829600000, 31.1282, 31.1282, 30.3398, 30.3398, 22.28],
                             [1559833200000, 30.7882, 30.7882, 30.7882, 30.7882, 4.06]]}
base_asset = 'BNB'
frequency = 200
target_return = None
target_risk = 0.01
weight_bounds = (0.05, 0.85)


class TestPortfolioOpt(unittest.TestCase):

    def setUp(self):
        self.po = PortfolioOpt()


class Test_make_weight_bounds(TestPortfolioOpt):
    def test_make_weight_bounds(self):
        self.assertEqual(True, True)


class Test_forward_looking_return(TestPortfolioOpt):
    def test_forward_looking_return(self):
        d_c = self.po.build_pricing_data_from_ohlcv(pricing_data, base_asset)
        r_b, r_e, e_f = self.po.generate_analysis_model(d_c, weight_bounds, frequency)
        if target_return is not None:
            _oer = e_f.efficient_return(target_return=target_return)
        if target_risk is not None:
            _omw = e_f.efficient_risk(target_risk=target_risk)
        w_c = e_f.clean_weights()
        a, b, c = self.po.forward_looking_return(d_c, r_b, r_e, w_c)
        self.assertEqual(a, 'Thu Jun  6 14:00:00 2019')
        self.assertEqual(b, 'Thu Jun  6 18:00:00 2019')
        self.assertEqual(c, 0.01827667022913032)


class Test_generate_analysis_model(TestPortfolioOpt):
    def test_generate_analysis_model(self):
        dc = self.po.build_pricing_data_from_ohlcv(pricing_data, base_asset)
        model = self.po.generate_analysis_model(dc, weight_bounds, frequency)
        self.assertIsInstance(model, tuple)


class Test_usdt_generate_report(TestPortfolioOpt):
    def test_usdt_generate_report(self):
        a, b = self.po.generate_report(pricing_data, weight_bounds,
                                       base_asset, frequency,
                                       target_risk, target_risk)
        self.assertDictEqual(a, {'BTC': 0.05, 'ETH': 0.05, 'USDT': 0.05, 'XRP': 0.05, 'PAX': 0.05,
                                 'TUSD': 0.05, 'USDC': 0.05, 'USDS': 0.05, 'BNB': 0.6})
        self.assertEqual(len(b), 5)


class Test_build_pricing_data_from_ohlcv(TestPortfolioOpt):
    def test_build_pricing_data_from_ohlcv_bnb_columns(self):
        dc = self.po.build_pricing_data_from_ohlcv(pricing_data, 'BNB')
        # Check for column names
        self.assertListEqual(list(dc.columns.values),
                             ['BTC', 'ETH', 'USDT', 'XRP', 'PAX', 'TUSD', 'USDC', 'USDS', 'BNB'])
        # Check for unique column names
        self.assertEqual(len(list(dc.columns.values)), len(set(dc.columns.values)))

    def test_build_pricing_data_from_ohlcv_bnb(self):
        dc = self.po.build_pricing_data_from_ohlcv(pricing_data, 'BNB')
        self.assertEqual(len(dc), 5)
        self.assertEqual(len(dc.columns), 9)

    def test_build_pricing_data_from_ohlcv_usdt(self):
        dc = self.po.build_pricing_data_from_ohlcv(pricing_data_2, 'USDT')
        # Check for unique column names
        self.assertEqual(len(list(dc.columns.values)), len(set(dc.columns.values)))
        self.assertEqual(len(dc), 3)
        self.assertEqual(len(dc.columns), 4)


if __name__ == '__main__':
    unittest.main()
