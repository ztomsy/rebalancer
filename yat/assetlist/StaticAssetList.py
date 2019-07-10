"""
Static Portfolio Assets List provider

Provides whitelist, blacklist, portfolio values

 """
from yat.assetlist.AssetList import AssetList


class StaticAssetList(AssetList):

    def __init__(self, logger, exchange, white_list: list, black_list: list, weight_bounds: tuple) -> None:
        super().__init__(logger, exchange, white_list, black_list, weight_bounds)

    def short_desc(self) -> str:
        """
        Short whitelist method description - used for startup-messages
        """
        return f"{self.name}: {self.portfolio}"

    def refresh_assetlist(self) -> None:
        """
        Refresh assetlists and assigns them to self._whitelist
        """
        portfolio_asset_list = self._validate_assetlist(self.whitelist)
        self._whitelist = portfolio_asset_list

    def build_portfolio_assets_markets(self, portfolio_base_asset: str) -> list:
        """
        Build new portfolio assets markets from validated whitelist and assign
        newly validated portfolio assets with weight_bounds to self._whitelist
        and self._portfolio respectively

        :param portfolio_base_asset: Base asset of portfolio
        :return: Markets list which will be used in portfolio calculation
        """
        p_b_markets, p_assets = self._build_portfolio_base_markets(portfolio_base_asset)
        self._portfolio = {x: self._weight_bounds for x in p_assets}
        self._whitelist = p_assets
        return p_b_markets
