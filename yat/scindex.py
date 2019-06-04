
def _calculate_index(exchange):
    overall_volume = 0
    index_ask_price = 0
    index_bid_price = 0
    for s in exchange.scindex_markets:
        overall_volume += exchange.all_tickers[s]['baseVolume']
    for s in exchange.scindex_markets:
        index_ask_price += exchange.all_tickers[s]['ask'] * exchange.all_tickers[s][
            'baseVolume'] / overall_volume
        index_bid_price += exchange.all_tickers[s]['bid'] * exchange.all_tickers[s][
            'baseVolume'] / overall_volume
    return overall_volume, index_ask_price, index_bid_price

def _count_sci_balance(exchange, asset):
    if asset == 'BTC':
        btc_balance = exchange.balances[asset]['all']
    else:
        btc_balance = exchange._count_btc_balance(exchange.balances[asset]['all'], asset)
    return btc_balance * (exchange.scindex_value['ask']+exchange.scindex_value['bid'])/2
