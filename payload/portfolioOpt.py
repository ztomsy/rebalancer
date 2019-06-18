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

    # region Helpers
    def elapsed_time(self):
        next_last_call = timer()
        elapsed = next_last_call - self.last_call
        self.last_call = next_last_call
        return elapsed

    @ staticmethod
    def as_days(date_string):
        if date_string is None: return None
        try:
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

    def progress(self, msg):
        return "({:.3f} sec) {}...".format(self.elapsed_time(), msg)

    # endregion

    # region Optimizer
    def generate_analysis_model(self, pricing_data, weight_bounds, frequency):
        mu = expected_returns.mean_historical_return(pricing_data, frequency=frequency)
        s = risk_models.sample_cov(pricing_data, frequency=frequency)
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

    def build_pricing_data_from_ohlcv(self, portfolio_ohlcv: dict, base_asset: str) -> dict:
        """
        Build new column names from market to asset name.

        Build new pricing dict from portfolio_ohlcv 'close' column
        and flip prices if necessary.

        Add base asset column with price equal to '1'.

        :param portfolio_ohlcv: Pricing data
        :type portfolio_ohlcv: dict
        :param base_asset: Base asset
        :type base_asset: str
        :return: Formated pricing data dict
        :rtype: dict
        """

        data_c = pd.DataFrame()
        for m, ohlcv in portfolio_ohlcv.items():
            data = numpy.array(ohlcv).transpose()
            data = {"date":   data[0], "o": data[1], "h": data[2],
                    "l": data[3], "c": data[4], "v": data[5]}
            data = pd.DataFrame(data)
            data["date"] = data["date"].apply(lambda x: ctime(x / 1000.0))
            data = data.set_index("date")
            asset1, asset2 = m.split('/')
            if asset1 != base_asset:
                data_c[asset1] = data['c']
            else:
                # Flip price for markets like asset/base_asset
                data_c[asset2] = data['c'].apply(lambda x: 1/x)

        # Add new column with 1 price for base asset
        data_c[base_asset] = 1
        return data_c

    def generate_report(self, pricing_data: dict = None, weight_bounds: tuple = None, base_asset: str = None,
                        frequency: int = None, target_return: float = None, target_risk: float = None):
        # Transform prices ohlcv data and add 1 price base asset column
        p_d = deepcopy(self.build_pricing_data_from_ohlcv(pricing_data, base_asset))
        # Generate EfficientFrontier Portfolio
        analysis_range_begin, analysis_range_end, ef = self.generate_analysis_model(
                p_d, weight_bounds, frequency)
        # Calculate the 'Markowitz portfolio', minimising volatility for a given target_return.
        # target_return: the desired return of the resulting portfolio
        if target_return is not None:
            _oer = ef.efficient_return(target_return=target_return)
        # Calculate the Sharpe-maximising portfolio for a given volatility(max return for a target_risk).
        # target_risk: the desired volatility of the resulting portfolio
        if target_risk is not None:
            _omw = ef.efficient_risk(target_risk=target_risk)
        # Minimise volatility
        # _raw_weights = ef.min_volatility()
        # Maximise the Sharpe Ratio
        # _raw_weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights(cutoff=1e-4, rounding=2)
        non_zero_weights = dict(filter(lambda w: w[1] > 0.0, cleaned_weights.items()))
        # Calculating sharpe ratios of above portfolio
        mu, sigma, sharpe = ef.portfolio_performance()
        # Calculating Returns
        range_begin, range_end, wavg_return = self.forward_looking_return(
            p_d,
            analysis_range_begin,
            analysis_range_end,
            non_zero_weights)
        # proper_weights = {x[0]: y for x, y in cleaned_weights.items()}
        # Prepare list to pass to ui api
        p_list = []
        p_list.append("Period: {} - {}".format(str(range_begin), str(range_end)))
        p_list.append("Bounds: {} Base: {} Freq: {}".format(weight_bounds, base_asset, frequency))
        p_list.append("Target return: {} Target_risk: {}".format(target_return, target_risk))
        p_list.append("Portfolio return: {:.2f}% Expected return: {:.2f}%".format(100 * wavg_return, 100 * mu))
        p_list.append("Volatility: {:>10.2f}% Sharpe Ratio: {:>7.2f}".format(100 * sigma, sharpe))
        # for key, value in sorted(non_zero_weights.items(), key=lambda kv: -kv[1]):
        #     p_list.append("{}: {:.2f}%".format(str(key[0]), 100 * value))
        # rebal_str = ["{}:{:.2f}%".format(str(k[0]), 100 * v) for k, v in sorted(non_zero_weights.items(),
        #                                                                          key=lambda kv: -kv[1])]
        # p_list.append(rebal_str)
        return cleaned_weights, p_list

    # endregion

    def make_weight_bounds(self, weight_bounds):
        # TODO Add separate bounds for each asset <class 'tuple'>: ((0, 0.6), (0.2, 1), (0, 0.1))

        pass