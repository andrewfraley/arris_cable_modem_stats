"""
    Influx functions

    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long

import logging
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError


def send_to_influx(stats, config):
    """ Send the stats to InfluxDB """
    logging.info('Sending stats to InfluxDB (%s:%s)', config['influx_host'], config['influx_port'])

    influx_client = InfluxDBClient(
        config['influx_host'],
        config['influx_port'],
        config['influx_username'],
        config['influx_password'],
        config['influx_database'],
        config['influx_use_ssl'],
        config['influx_verify_ssl'],
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
        influx_client.write_points(series)
    except (InfluxDBClientError, ConnectionError, InfluxDBServerError, ConnectionRefusedError) as exception:

        # If DB doesn't exist, try to create it
        if hasattr(exception, 'code') and exception.code == 404:
            logging.warning('Database %s Does Not Exist.  Attempting to create database',
                            config['influx_database'])
            influx_client.create_database(config['influx_database'])
            influx_client.write_points(series)
        else:
            logging.error(exception)
            logging.error('Failed To Write To InfluxDB')
            return

    logging.info('Successfully wrote data to InfluxDB')
    logging.debug('Influx series sent to db:')
    logging.debug(series)
