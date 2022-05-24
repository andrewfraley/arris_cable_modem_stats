"""
    Influx 2.x functions

    https://github.com/andrewfraley/arris_cable_modem_stats

    Thank you to Chris Schuld (https://github.com/cbschuld) for the Influx 2.x changes

"""
# pylint: disable=line-too-long

import logging
from datetime import datetime
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS


def send_to_influx(stats, config):
    """ Send the stats to InfluxDB """
    logging.info('Sending stats to InfluxDB (%s:%s)', config['influx_host'], config['influx_port'])

    influx_client = InfluxDBClient(
        url=config['influx_url'],
        token=config['influx_token'],
        org=config['influx_org'],
        bucket=config['influx_bucket'],
        verify_ssl=config['influx_verify_ssl'],
    )

    series = []
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    for stats_down in stats['downstream']:
        record = {
            'measurement': 'downstream_statistics',
            'time': current_time,
            'fields': {},
            'tags': {
                'channel_id': int(stats_down['channel_id'])
            }
        }
        for field in stats_down:
            if field == 'channel_id':
                continue
            if '.' in stats_down[field]:
                record['fields'][field] = float(stats_down[field])
            else:
                record['fields'][field] = int(stats_down[field])
        series.append(record)

    for stats_up in stats['upstream']:
        record = {
            'measurement': 'upstream_statistics',
            'time': current_time,
            'fields': {},
            'tags': {
                'channel_id': int(stats_up['channel_id'])
            }
        }
        for field in stats_up:
            if field == 'channel_id':
                continue
            if '.' in stats_up[field]:
                record['fields'][field] = float(stats_up[field])
            else:
                record['fields'][field] = int(stats_up[field])
        series.append(record)

    try:
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(record=series, bucket=config['influx_bucket'])
    except (InfluxDBError, ConnectionError, ConnectionRefusedError) as exception:
        logging.error('Failed To Write To InfluxDB')
        logging.error(exception)
        return

    logging.info('Successfully wrote data to InfluxDB')
    logging.debug('Influx series sent to db:')
    logging.debug(series)

    influx_client.close()
