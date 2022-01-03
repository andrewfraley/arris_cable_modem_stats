"""
    Influx functions

    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long

import logging
from datetime import datetime
from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS

def send_to_influx(stats, config):
    """ Send the stats to InfluxDB """
    logging.info('Sending stats to InfluxDB (%s)', config['influx_url'])

    token = config['influx_token']
    url = config['influx_url']
    org = config['influx_org']
    bucket = config['influx_bucket']
    verify_ssl = config['influx_verify_ssl']

    influx_client = InfluxDBClient(
        url=url,
        token=token,
        org=org,
        bucket=bucket,
        verify_ssl=verify_ssl
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

    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    try:
        write_api.write(record=series,bucket=config['influx_bucket'])

    except (InfluxDBError, ConnectionError, ConnectionRefusedError) as exception:

        # If bucket doesn't exist, try to create it
        if hasattr(exception, 'code') and exception.code == 404:
            logging.warning('Bucket %s Does Not Exist.  Attempting to create bucket', config['influx_bucket'])
            buckets_api = influx_client.buckets_api()
            retention_rules = BucketRetentionRules(type="expire", every_seconds=0)
            buckets_api.create_bucket(bucket_name=config['influx_bucket'], retention_rules=retention_rules, org=org)
            write_api.write(record=series,bucket=config['influx_bucket'])

        else:
            logging.error(exception)
            logging.error('Failed To Write To InfluxDB')
            return

    logging.info('Successfully wrote data to InfluxDB')
    logging.debug('Influx series sent to db:')
    logging.debug(series)

    influx_client.close()