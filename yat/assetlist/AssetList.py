"""
Asset List provider

Provides whitelist, blacklist values

 """
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple


class AssetList(ABC):

    def __init__(self, logger, exchange, white_list: list, black_list: list, weight_bounds: tuple) -> None:
        self.logger = logger
        self._exchange = exchange
        self._whitelist = white_list
        self._blacklist = black_list
        self._weight_bounds = weight_bounds
        self._portfolio = dict()

    @property
    def name(self) -> str:
        """
        Gets name of the class
        -> no need to overwrite in subclasses
        """
        return self.__class__.__name__

    @property
    def whitelist(self) -> List[str]:
        """
        Has the current whitelist
        -> no need to overwrite in subclasses
        """
        return self._whitelist

    @property
    def blacklist(self) -> List[str]:
        """
        Has the current blacklist
        -> no need to overwrite in subclasses
        """
        return self._blacklist

    @property
    def portfolio(self) -> Dict[(str, Tuple)]:
        """
        Has the current portfolio
        -> no need to overwrite in subclasses
        """
        return self._portfolio

    @abstractmethod
    def short_desc(self) -> str:
        """
        Short whitelist method description - used for startup-messages
        -> Please overwrite in subclasses
        """

    @abstractmethod
    def refresh_assetlist(self) -> None:
        """
        Refresh assetlists and assigns them to self._whitelist
        -> Please overwrite in subclasses
        """

    @abstractmethod
    def build_portfolio_assets_markets(self, portfolio_base_asset: str) -> List[str]:
        """
        Build new portfolio assets markets from validated whitelist and assign
        newly validated portfolio assets and weight_bounds to self._whitelist
        and self._portfolio respectively and return portfolio_base_markets.
        -> Please overwrite in subclasses
        """

    def _validate_assetlist(self, assetlist: List[str]) -> List[str]:
        """
        Check available markets and remove pair from whitelist if necessary

        :param assetlist: the sorted list of assets the user might want to have in portfolio
        :return: list of assets the user wants to have in portfolio without those
        unavailable or black_listed
        """
        markets = self._exchange.markets
        # Create filtered all asset list from markets
        sanitized_all_assetslist = set(a for m in markets.keys() for a in m.split('/'))

        sanitized_assetlist = set()
        for asset in assetlist:
            # asset is not in the generated dynamic assets list, or in the blacklist ... ignore it
            if asset in self.blacklist or asset not in sanitized_all_assetslist:
                self.logger.warning(f"Asset {asset} is not compatible with exchange "
                                    f"{self._exchange.exchange.id} or contained in "
                                    f"your blacklist. Removing it from whitelist..")
                continue
            sanitized_assetlist.add(asset)

        return list(sanitized_assetlist)

    def _build_portfolio_base_markets(self, portfolio_base_asset: str) -> Tuple[List[str], List[str]]:
        """
        Build new assets and define available markets for them

        :param portfolio_base_asset: base asset of portfolio
        :return: Markets list and new filtered assets list
        """
        portfolio_assets = self.whitelist
        markets = self._exchange.markets

        pa_list = set()
        pbm_list = set()
        for x, y in markets.items():
            if y['base'] in portfolio_assets and y['quote'] == portfolio_base_asset:
                pbm_list.add(x)
                pa_list.add(y['base'])
                portfolio_assets.remove(y['base'])
            elif y['quote'] in portfolio_assets and y['base'] == portfolio_base_asset:
                pbm_list.add(x)
                pa_list.add(y['quote'])
                portfolio_assets.remove(y['quote'])
        if len(portfolio_assets) > 0:
            for a in portfolio_assets:
                if f'{a}/BTC' in markets.keys():
                    pbm_list.add(f'{a}/BTC')
                    pa_list.add(a)
                elif f'BTC/{a}' in markets.keys():
                    pbm_list.add(f'BTC/{a}')
                    pa_list.add(a)
            if f'{portfolio_base_asset}/BTC' in markets.keys():
                pbm_list.add(f'{portfolio_base_asset}/BTC')
            elif f'BTC/{portfolio_base_asset}' in markets.keys():
                pbm_list.add(f'BTC/{portfolio_base_asset}')
        pa_list.add(portfolio_base_asset)

        return list(pbm_list), list(pa_list)
