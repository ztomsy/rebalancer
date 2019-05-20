#!/usr/bin/env python
# encoding: utf-8

class Trader(object):
    '''
    Trader generates quotes (dicts).
    Check for quote min quantity.
    A general base class for specific trader types.
    Public attributes: quote_collector, trader_type
    Public methods: none
    '''

    def __init__(self, name, maxq, minq):
        '''
        Initialize Trader with some base class attributes.
        quote_collector is a public container for carrying quotes to the exchange
        _trader_id as name
        _max_quantity and _min_quantity is provided in settings
        _quote_sequence is used for generating unique order id per Trader
        '''
        self._trader_id = name
        self.trader_type = 'Trader'
        self._max_quantity = maxq
        self._min_quantity = minq
        self.quote_collector = []
        self._quote_sequence = 0
        
    def __repr__(self):
        return 'Trader({0}-{1}-{2})'.format(self._trader_id, self._max_quantity, self._min_quantity)
        
    def _make_add_quote(self, step, quantity, side, price):
        '''
        Make one add quote (dict)
        Ignore quantities lower then minq
        :return: <class 'dict'>: {'order_id': '30001', 'timestamp': 62, 'type': 'add',
         'quantity': 0.0083, 'side': 'buy', 'price': 3862.86}
        '''
        self._quote_sequence += 1
        order_id = '%s%d' % (self._trader_id, self._quote_sequence)
        # Check for _min_quantity, ignore adding if lower then minq
        if quantity >= self._min_quantity:
            return {'order_id': order_id, 'step': step, 'type': 'add', 'quantity': quantity,
                    'side': side, 'price': price}
        else:
            return {}