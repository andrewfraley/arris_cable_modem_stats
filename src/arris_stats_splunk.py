
"""
    Splunk functions

    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long

import logging
from splunk_hec_handler import SplunkHecHandler


def send_to_splunk(stats, config):
    """ Send the stats to splunk """

    # Using this splunk log handler this way is a little odd, but the simplest and most
    # robust method I've seen for getting some random object data into splunk via the HTTP Event Collector
    # https://pypi.org/project/splunk-hec-handler/

    if config['splunk_ssl']:
        protocol = 'https'
    else:
        protocol = 'http'

    logger = logging.getLogger('SplunkHecHandlerExample')
    logger.setLevel(logging.DEBUG)

    # If using self-signed certificate, set ssl_verify to False
    # If using http, set proto to http
    splunk_handler = SplunkHecHandler(
        config['splunk_host'],
        config['splunk_token'],
        port=config['splunk_port'],
        proto=protocol,
        ssl_verify=config['splunk_verify_ssl'],
        source=config['splunk_source'],
        sourcetype='_json'
    )

    logger.addHandler(splunk_handler)
    logger.info(stats)
    logging.info('Successfully wrote data to Splunk')
    logging.debug('Stats sent to Splunk:')
    logging.debug(stats)
