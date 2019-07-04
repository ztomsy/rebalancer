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

    def progress(self, msg):
        return "({:.3f} sec) {}...".format(self.elapsed_time(), msg)

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

    # endregion

    # region Optimizer
    def generate_analysis_model(self, pricing_data, weight_bounds, exp_return_periods, risk_model_periods):
        """Generate efficient frontier model

        :param pricing_data: Adjusted closing prices of the asset, each row is a date
                   and each column is a ticker/id.
        :param weight_bounds: Minimum and maximum weight of an asset
        :param exp_return_periods: Number of time periods for expected returns for each asset.
                                 Set to None if optimising for volatility only.
        :param risk_model_periods: Number of time periods for covariance of returns for each asset.
        :return:
        """
        mu = expected_returns.mean_historical_return(pricing_data, frequency=exp_return_periods)
        s = risk_models.sample_cov(pricing_data, frequency=risk_model_periods)
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

    def build_pricing_data_from_ohlcv(self, ohlcv_data: dict, base_asset: str, time_frame: str):
        """
        Build new column names from market to asset name.

        Build new pricing dict from ohlcv_data 'close' column
        and flip prices if necessary.

        Add base asset column with price equal to '1'.

        :param ohlcv_data: Pricing data
        :type ohlcv_data: dict
        :param base_asset: Base asset
        :type base_asset: str
        :param time_frame: Time frame to choose from ohlcv_data, 1m..1h..etc.
        :type time_frame: str
        :return: Formated pricing data dict
        """
        data_c = pd.DataFrame()
        for m, ohlcv in ohlcv_data.items():
            if base_asset in m:
                asset1, asset2 = m.split('/')
                a_np = numpy.array(ohlcv[time_frame]).transpose()
                a_np = {"date":   a_np[0], "o": a_np[1], "h": a_np[2],
                        "l":      a_np[3], "c": a_np[4], "v": a_np[5]}
                data = pd.DataFrame(a_np)
                data["date"] = data["date"].apply(lambda x: ctime(x / 1000.0))
                data = data.set_index("date")
                if asset1 != base_asset:
                    data_c[asset1] = data['c']
                else:
                    # Flip price for markets like asset/base_asset
                    data_c[asset2] = data['c'].apply(lambda x: 1/x)
            else:
                # 2-leg markets
                if '/BTC' in m:
                    asset1, _ = m.split('/')
                    a_np = numpy.array(ohlcv[time_frame]).transpose()
                    if f'BTC/{base_asset}' in ohlcv_data.keys():
                        btc_np = numpy.array(ohlcv_data[f'BTC/{base_asset}'][time_frame]).transpose()
                        a_np = {"date": a_np[0], "o": a_np[1],           "h": a_np[2],
                                "l":    a_np[3], "c": a_np[4]*btc_np[4], "v": a_np[5]}
                    elif f'{base_asset}/BTC' in ohlcv_data.keys():
                        btc_np = numpy.array(ohlcv_data[f'{base_asset}/BTC'][time_frame]).transpose()
                        a_np = {"date": a_np[0], "o": a_np[1],           "h": a_np[2],
                                "l":    a_np[3], "c": a_np[4]/btc_np[4], "v": a_np[5]}
                    data = pd.DataFrame(a_np)
                    data["date"] = data["date"].apply(lambda x: ctime(x / 1000.0))
                    data = data.set_index("date")
                    data_c[asset1] = data['c']
                elif 'BTC/' in m:
                    _, asset2 = m.split('/')
                    a_np = numpy.array(ohlcv[time_frame]).transpose()
                    if f'BTC/{base_asset}' in ohlcv_data.keys():
                        btc_np = numpy.array(ohlcv_data[f'BTC/{base_asset}'][time_frame]).transpose()
                        a_np = {"date": a_np[0], "o": a_np[1],           "h": a_np[2],
                                "l":    a_np[3], "c": a_np[4]/btc_np[4], "v": a_np[5]}
                    elif f'{base_asset}/BTC' in ohlcv_data.keys():
                        btc_np = numpy.array(ohlcv_data[f'{base_asset}/BTC'][time_frame]).transpose()
                        a_np = {"date": a_np[0], "o": a_np[1],           "h": a_np[2],
                                "l":    a_np[3], "c": a_np[4]*btc_np[4], "v": a_np[5]}
                    data = pd.DataFrame(a_np)
                    data["date"] = data["date"].apply(lambda x: ctime(x / 1000.0))
                    data = data.set_index("date")
                    data_c[asset2] = data['c']

        # Add new column with 1 price for base asset
        data_c[base_asset] = 1
        return data_c

    def generate_report(self, ohlcv_data: dict = None, time_frames: list = None,
                        weight_bounds: tuple = None, base_asset: str = None,
                        exp_return_periods: int = None, risk_model_periods: int = None,
                        target_return: float = None, target_risk: float = None):
        # Transform ohlcv data into pricing data and add 1 price base asset column
        # Multiple timeframes data creation controlled from time_frames list
        p_d = deepcopy(self.build_pricing_data_from_ohlcv(ohlcv_data, base_asset, time_frames[0]))
        # Generate EfficientFrontier Portfolio
        analysis_range_begin, analysis_range_end, ef = self.generate_analysis_model(
                p_d, weight_bounds, exp_return_periods, risk_model_periods)
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
        p_list.append("Bounds: {} Base: {}".format(weight_bounds, base_asset))
        p_list.append("Return periods: {} Risk model periods: {}".format(exp_return_periods, risk_model_periods))
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

    def _update_pctchange_data(self, p_bm, p_ohlcv, p_tf) -> None:
        # Does not used atm.
        self.pctchange_data.clear()
        self.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%']]
        for m in p_bm:
            p = p_ohlcv[m][p_tf[0]][-1][4]
            self.pctchange_data.append([m, 'binance',
                                        "{:+.2f}".format(100*(p-p_ohlcv[m][p_tf[0]][-2][4])/p),
                                        "{:+.2f}".format(100*(p-p_ohlcv[m][p_tf[0]][-4][4])/p),
                                        "{:+.2f}".format(100*(p-p_ohlcv[m][p_tf[0]][-13][4])/p),
                                        "{:+.2f}".format(100*(p-p_ohlcv[m][p_tf[0]][-25][4])/p),
                                        "{:+.2f}".format(100*(p-p_ohlcv[m][p_tf[0]][-73][4])/p)])
