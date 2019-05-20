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
            print('Connection to InfluxDB failed: ', type(e).__name__, "-=-=-", e.args, '-=-=-', str(e))

    def _write_points(self, points=None, time_precision=None, database=None, protocol='json'):
        try:
            self.client.write_points(points,
                                     time_precision=time_precision,
                                     database=database,
                                     protocol=protocol)
        except Exception as e:
            print('Writing data to InfluxDB failed: ', type(e).__name__, "-=-=-", e.args, '-=-=-', str(e))

    def _query(self, query='', database=None, chunked=False, chunk_size=0):
        try:
            return self.client.query(query=query,
                                     database=database,
                                     chunked=chunked,
                                     chunk_size=chunk_size)
        except Exception as e:
            print('Querying data from InfluxDB failed: ', type(e).__name__, "-=-=-", e.args, '-=-=-', str(e))

