
def _calculate_index(self):
    overall_volume = 0
    index_ask_price = 0
    index_bid_price = 0
    for s in self.scindex_markets:
        overall_volume += self.exchange1.all_tickers[s]['baseVolume']
    for s in self.scindex_markets:
        index_ask_price += self.exchange1.all_tickers[s]['ask'] * self.exchange1.all_tickers[s][
            'baseVolume'] / overall_volume
        index_bid_price += self.exchange1.all_tickers[s]['bid'] * self.exchange1.all_tickers[s][
            'baseVolume'] / overall_volume
    return overall_volume, index_ask_price, index_bid_price

def _count_sci_balance(self, asset):
    if asset == 'BTC':
        btc_balance = self.balances[asset]['all']
    else:
        btc_balance = self._count_btc_balance(self.balances[asset]['all'], asset)
    return btc_balance * (self.scindex_value['ask']+self.scindex_value['bid'])/2
