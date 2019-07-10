from influxdb import InfluxDBClient


class Influx(object):

    def __init__(self, host='localhost', port=8086, username='root', password='root', database=None):
        try:
            self.client = InfluxDBClient(host=host,
                                         port=port,
                                         username=username,
                                         password=password,
                                         database=database)
        except Exception as e:
            raise RuntimeError('Connection to InfluxDB failed') from e

    def _write_points(self, points=None, time_precision=None, database=None, protocol='json'):
        try:
            self.client.write_points(points,
                                     time_precision=time_precision,
                                     database=database,
                                     protocol=protocol)
        except Exception as e:
            raise RuntimeError('Writing data to InfluxDB failed') from e

    def _query(self, query='', database=None, chunked=False, chunk_size=0):
        try:
            return self.client.query(query=query,
                                     database=database,
                                     chunked=chunked,
                                     chunk_size=chunk_size)
        except Exception as e:
            raise RuntimeError('Querying data from InfluxDB failed') from e

    def report_order(self, order: dict, provider: str, exchange: str):
        """
        Prepare order dict to supported json format and write it with provided client

        :param order:
        :param provider:
        :param exchange:
        :return:
        """
        prepared_order = dict()
        prepared_order['measurement'] = 'orders_data'
        prepared_order['tags'] = {'provider': provider,
                                  'exchange': exchange}
        prepared_order['fields'] = dict(id=order['id'],
                                        timestamp=order['timestamp'],
                                        symbol=order['symbol'],
                                        type=order['type'],
                                        side=order['side'],
                                        price=order['price'],
                                        amount=order['filled'],
                                        status=order['status'],
                                        fee=order['fee'],)
        self._write_points([prepared_order, ])

    def report_market_state(self, market_state: dict):
        p_state = dict()
        p_state['measurement'] = 'market_state_data'
        p_state['tags'] = {'ticker': market_state['ticker'],
                           'exchange': market_state['exchange']}
        p_state['fields'] = dict(param1=market_state['param1'],
                                 param2=market_state['param2'],)
        self._write_points(p_state)
