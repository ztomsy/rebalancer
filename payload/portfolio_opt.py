import math
import datetime
from time import ctime
from copy import deepcopy
import pandas as pd
import numpy
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns

from timeit import default_timer as timer



class PortfolioOpt:

    def __init__(self):
        self.start = timer()
        self.last_call = self.start
        self.cutoff_date = datetime.datetime.now()
        self.weight_bound: float = 0
        self.return_months: int = 0

    # region Helpers
    def elapsed_time(self):
        next_last_call = timer()
        elapsed = next_last_call - self.last_call
        self.last_call = next_last_call
        return elapsed

    @ staticmethod
    def as_date(date_string):
        if date_string is None: return None
        try:
            # TODO make it available for different time format
            return datetime.datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            return None

    @ staticmethod
    def as_pct(float_string):
        if float_string is None: return None
        try:
            return float(float_string) / 100.0
        except ValueError:
            return None

    @ staticmethod
    def as_int(int_string):
        if int_string is None: return None
        try:
            return int(int_string)
        except ValueError:
            return None

    @ staticmethod
    def months_from_date(start_date, months_offset):
        # TODO make it available for different time format
        year, month, day = start_date.timetuple()[:3]
        new_month = month + months_offset
        return datetime.date(year + math.floor(new_month / 12), (new_month % 12) or 12, day)

    def progress(self, msg):
        return "({:.3f} sec) {}...".format(self.elapsed_time(), msg)

    # endregion

    # region Optimizer
    def generate_analysis_model(self, pricing_data, weight_bounds):
        self.progress('Processing Pricing')
        # TODO Now only works with 1h data
        mu = expected_returns.mean_historical_return(pricing_data, 7*24)
        s = risk_models.sample_cov(pricing_data, 7*24)

        range_begin = pricing_data.index[0]
        range_end = pricing_data.index[-1]

        return range_begin, range_end, EfficientFrontier(mu, s, weight_bounds=weight_bounds, gamma=0)

    def forward_looking_return(self, pricing_data, start_date, end_date, weights):
        df_pricing = pricing_data \
            .loc[start_date:end_date] \
            .dropna(axis=1, how='any') \
            .iloc[[0, -1]]

        df_weights = pd.DataFrame([weights])
        pricing_changes = df_pricing.pct_change()
        filtered_pricing = pricing_changes.tail(1).filter(axis=1, items=weights.keys())

        range_begin, range_end = pricing_changes.index.values
        wavg_return = (df_weights.values * filtered_pricing.values).sum()

        return range_begin, range_end, wavg_return

    def build_pricing_data_from_ohlcv(self, portfolio_ohlcv: dict, assets_list: list):
        """
        >>> pricing_data =  {'BTC/USDT': [[1258317600000, 7965.08, 7966.78, 7830.0, 7889.32, 1755.837013],[1258321200000, 7889.33, 8067.3, 7885.85, 8030.04, 2082.664391]],'ETH/USDT': [[1258317600000, 250.07, 250.08, 246.0, 247.57, 26873.12446],[1258321200000, 247.6, 254.65, 247.27, 254.05, 27160.78046]]}
        >>> po = PortfolioOpt()
        >>> po.build_pricing_data_from_ohlcv(pricing_data).info()
        <class 'pandas.core.frame.DataFrame'>
        Index: 2 entries, Sun Nov 15 23:40:00 2009 to Mon Nov 16 00:40:00 2009
        Data columns (total 2 columns):
        BTC/USDT    2 non-null float64
        ETH/USDT    2 non-null float64
        dtypes: float64(2)
        memory usage: 48.0+ bytes

        :param portfolio_ohlcv:
        :return:
        """
        # assets_list = [x for x in portfolio_ohlcv.keys()]
        data_c = pd.DataFrame()
        for i, j in portfolio_ohlcv.items():
            data = j
            data = numpy.array(data)
            data = data.transpose()
            data = {"date":   data[0], "o": data[1], "h": data[2],
                    "l": data[3], "c": data[4], "v": data[5]}
            data = pd.DataFrame(data)
            data["date"] = data["date"].apply(lambda x: ctime(x / 1000.0))
            data = data.set_index("date")
            data_c[i] = data['c']
        # FIXME Check for assets_list and markets proper name
        data_c.columns = [assets_list]
        return data_c

    def generate_report(self, pricing_data, weight_bounds, assets_list):
        p_d = deepcopy(self.build_pricing_data_from_ohlcv(pricing_data, assets_list))
        # TODO Add separate bounds for each asset <class 'tuple'>: ((0, 0.6), (0.2, 1), (0, 0.1))
        analysis_range_begin, analysis_range_end, ef = self.generate_analysis_model(p_d, weight_bounds)
        # Optimise for maximal Sharpe ratio
        # print(self.progress('Choosing securities'))
        # _omw = ef.efficient_risk(target_risk=0.1)
        _raw_weights = ef.min_volatility()
        cleaned_weights = ef.clean_weights()
        non_zero_weights = dict(filter(lambda w: w[1] > 0.0, cleaned_weights.items()))
        # print(self.progress('Calculating sharpe ratios'))
        mu, sigma, sharpe = ef.portfolio_performance()
        # _mu, sigma, sharpe = ef.portfolio_performance(verbose=True)
        # print(self.progress('Calculating Returns'))
        range_begin, range_end, wavg_return = self.forward_looking_return(
            p_d,
            analysis_range_begin,
            analysis_range_end,
            non_zero_weights)

        p_list = [str("Expected return for period: {:.2f}%".format(100 * mu)), ]
        p_list.append("Portfolio Return ({}...{}): {:.2f}%".format(str(range_begin), str(range_end), 100 * wavg_return))
        p_list.append("Volatility: {:.2f}%".format(100 * sigma))
        p_list.append("Sharpe Ratio: {:.2f}".format(sharpe))
        for key, value in sorted(non_zero_weights.items(), key=lambda kv: -kv[1]):
            p_list.append("{}: {:.2f}%".format(str(key[0]), 100 * value))
        #
        # print('(done in {:.3f} seconds)'.format(datetime.timedelta(seconds=self.elapsed_time()).total_seconds()))
        #
        return non_zero_weights, p_list

    # endregion
