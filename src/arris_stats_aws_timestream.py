"""
    AWS Timestream functions

    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long
import logging
import boto3
from botocore.config import Config


def send_to_aws_time_stream(stats, config):
    """ Send the stats to AWS Timestream """
    logging.info('Sending stats to Timestream (database=%s)', config['timestream_database'])

    region_config = Config(
        region_name=config['timestream_aws_region']
    )

    ts_client = boto3.client(
        'timestream-write',
        aws_access_key_id=config['timestream_aws_access_key_id'],
        aws_secret_access_key=config['timestream_aws_secret_access_key'],
        config=region_config
    )

    try:
        # Attempt to validate connection to database and table
        # Error out and return if not able to access / connection isn't valid
        database = ts_client.describe_database(
            DatabaseName=config['timestream_database']
        )
        logging.debug("Database details = %s" % database)

        table = ts_client.describe_table(
            DatabaseName=config['timestream_database'],
            TableName=config['timestream_table']
        )
        logging.debug("Table details = %s" % table)
    except Exception as err:
        logging.error(err)
        return

    current_time = time.time_ns()
    logging.debug("Converting to timestream - %s" % stats)

    downstream_common_attributes = {
        'Dimensions': [{'Name': 'measurement', 'Value': 'downstream_statistics'}],
        'Time': str(current_time),
        'TimeUnit': 'NANOSECONDS'
    }
    downstream_records = []
    for stats_down in stats['downstream']:
        for key in stats_down:
            if key == 'channel_id':
                continue

            downstream_records.append({
                'Dimensions': [
                    {'Name': 'channel_id', 'Value': str(stats_down['channel_id'])},
                    {'Name': 'group', 'Value': 'downstream_statistics'}
                ],
                'MeasureName': key,
                'MeasureValue': str(stats_down[key]),
                'MeasureValueType': 'DOUBLE' if isinstance(stats_down[key], float) else 'BIGINT'
            })

    try:
        logging.debug("Writing common attributes: %s" % downstream_common_attributes)
        logging.debug("Writing records: %s" % downstream_records)
        result = ts_client.write_records(DatabaseName=config['timestream_database'],
                                         TableName=config['timestream_table'], Records=downstream_records,
                                         CommonAttributes=downstream_common_attributes)
        logging.info("Timestream response = %s" % result)
        logging.info("Wrote %s records to TimeStream" % len(downstream_records))
    except (ts_client.exceptions.RejectedRecordsException, Exception) as err:
        logging.error(err)

    upstream_common_attributes = {
        'Dimensions': [{'Name': 'measurement', 'Value': 'upstream_statistics'}],
        'Time': str(current_time),
        'TimeUnit': 'NANOSECONDS'
    }
    upstream_records = []
    for stats_up in stats['upstream']:
        for key in stats_up:
            if key == 'channel_id':
                continue

            upstream_records.append({
                'Dimensions': [
                    {'Name': 'channel_id', 'Value': str(stats_up['channel_id'])},
                    {'Name': 'group', 'Value': 'upstream_statistics'}
                ],
                'MeasureName': key,
                'MeasureValue': str(stats_up[key]),
                'MeasureValueType': 'DOUBLE' if isinstance(stats_up[key], float) else 'BIGINT'
            })

    try:
        logging.debug("Writing common attributes: %s" % upstream_common_attributes)
        logging.debug("Writing records: %s" % upstream_records)
        result = ts_client.write_records(DatabaseName=config['timestream_database'],
                                         TableName=config['timestream_table'], Records=upstream_records,
                                         CommonAttributes=upstream_common_attributes)
        logging.info("Timestream response = %s" % result)
        logging.info("Wrote %s records to TimeStream" % len(upstream_records))
    except (ts_client.exceptions.RejectedRecordsException, Exception) as err:
        logging.error(err)
        return

    logging.info('Successfully wrote data to Timestream')
