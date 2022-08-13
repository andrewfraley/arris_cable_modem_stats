"""
    Pull stats from Arris Cable modem's web interface
    Send stats to InfluxDB

    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long

import os
import sys
import time
import base64
import logging
import argparse
import configparser
import urllib3
import requests
import json

# To add a new modem, add the model below
# Create a new file src/arris_stats_themodel.py and a parse_html_themodel.py function
# Use a debugger and set a break point just after the html = get_html(config, credential) line
# Set another break point just after the  stats = parse_html_function(html) line
# Save the raw html to tests/mockups/themodel.html
# Save the stats dict as json to tests/mockups/themodel.json
# The unittests will automatically pickup the new model, function, and mockups.  Ensure the tests pass with:
# bash tests/run_tests.sh
modems_supported = [
    'sb8200',
    'sb6183',
    't25'
]


def main():
    """ MAIN """

    args = get_args()
    config_path = args.config
    config = get_config(config_path)

    init_logger(args.log_level or config.get('log_level'))

    sleep_interval = int(config['sleep_interval'])
    destination = config['destination']

    # Disable the SSL warnings if we're not verifying SSL
    if not config['modem_verify_ssl']:
        urllib3.disable_warnings()

    # SB8200 requires authentication on Comcast now
    token = None
    session = requests.Session()

    first = True
    while True:
        if not first:
            logging.info('Sleeping for %s seconds', sleep_interval)
            sys.stdout.flush()
            time.sleep(sleep_interval)
        first = False

        if config['modem_auth_required']:
            while not token:
                token_func = config['get_token_function'] or get_token
                token = token_func(config, session)
                if not token and config['exit_on_auth_error']:
                    error_exit('Unable to authenticate with modem.  Exiting since exit_on_auth_error is True', config)
                if not token:
                    logging.info('Unable to obtain valid login session, sleeping for: %ss', sleep_interval)
                    time.sleep(sleep_interval)

        # Get the HTML from the modem
        html = get_html(config, token, session)
        if not html:
            if config['exit_on_html_error']:
                error_exit('No HTML obtained from modem.  Exiting since exit_on_html_error is True', config)
            logging.error('No HTML to parse, giving up until next interval')
            if config['clear_auth_token_on_html_error']:
                logging.info('clear_auth_token_on_html_error is true, clearing credential token')
                token = None
                session = requests.Session()
            continue

        # Get the function reference from the config dict
        parse_html_function = config['parse_html_function']
        stats = parse_html_function(html)

        if not stats or (not stats['upstream'] and not stats['downstream']):
            logging.error(
                'Failed to get any stats, giving up until next interval')
            continue

        # Where should 6we send the results?
        if destination == 'influxdb' and config['influx_major_version'] == 1:
            import arris_stats_influx1  # pylint: disable=import-outside-toplevel
            arris_stats_influx1.send_to_influx(stats, config)
        elif destination == 'influxdb' and config['influx_major_version'] == 2:
            import arris_stats_influx2  # pylint: disable=import-outside-toplevel
            arris_stats_influx2.send_to_influx(stats, config)
        elif destination == 'timestream':
            import arris_stats_aws_timestream  # pylint: disable=import-outside-toplevel
            arris_stats_aws_timestream.send_to_aws_time_stream(stats, config)
        elif destination == 'splunk':
            import arris_stats_splunk  # pylint: disable=import-outside-toplevel
            arris_stats_splunk.send_to_splunk(stats, config)
        elif destination == 'stdout_json':
            print(json.dumps(stats))
        else:
            error_exit('Destination %s not supported!  Aborting.' % destination, sleep=False)


def get_args():
    """ Get argparser args """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', metavar='config_file_path', help='Path to config file', required=False)
    parser.add_argument('--debug', help='Enable debug logging', action='store_true', required=False, default=False)
    parser.add_argument('--log-level', help='Set log_level', action='store', type=str.lower, required=False, choices=["debug", "info", "warning", "error"])
    args = parser.parse_args()
    if args.debug:
        args.log_level = "debug"
    return args


def get_default_config():
    return {

        # Main
        'log_level': "info",
        'destination': 'influxdb',
        'sleep_interval': 300,
        'modem_url': 'https://192.168.100.1/cmconnectionstatus.html',
        'modem_verify_ssl': False,
        'modem_auth_required': False,
        'modem_username': 'admin',
        'modem_password': None,
        'modem_model': 'sb8200',
        'exit_on_auth_error': True,
        'exit_on_html_error': True,
        'clear_auth_token_on_html_error': True,
        'sleep_before_exit': True,

        # Influx
        'influx_major_version': 1,
        'influx_host': 'localhost',
        'influx_port': 8086,
        'influx_database': 'cable_modem_stats',
        'influx_username': None,
        'influx_password': None,
        'influx_use_ssl': False,
        'influx_verify_ssl': True,
        'influx_org': None,
        'influx_url': 'http://localhost:8086',
        'influx_bucket': 'cable_modem_stats',
        'influx_token': None,

        # AWS Timestream
        'timestream_aws_access_key_id': None,
        'timestream_aws_secret_access_key': None,
        'timestream_database': 'cable_modem_stats',
        'timestream_table': 'cable_modem_stats',
        'timestream_aws_region': 'us-east-1',

        # Splunk
        'splunk_token': None,
        'splunk_host': None,
        'splunk_port': 8088,
        'splunk_ssl': False,
        'splunk_verify_ssl': True,
        'splunk_source': 'arris_cable_modem_stats'
    }


def get_config(config_path=None):
    """ Grab config from the ini config file,
        then grab the same variables from ENV to override
    """

    default_config = get_default_config()
    config = default_config.copy()

    # Get config from config.ini if specified
    if config_path:
        logging.info('Getting config from: %s', config_path)
        # Some hacky action to get the config without using section headings in the file
        # https://stackoverflow.com/a/10746467/866057
        parser = configparser.RawConfigParser()
        section = 'MAIN'
        with open(config_path) as fileh:
            file_content = '[%s]\n' % section + fileh.read()
        parser.read_string(file_content)

        for param in default_config:
            config[param] = parser[section].get(param, default_config[param])
    else:  # Get it from ENV
        logging.info('Getting config from ENV')
        for param in config:
            if os.environ.get(param):
                config[param] = os.environ.get(param)

    # Special handling depending ontype
    for param in config:

        # If the default value is a boolean, but we have a string, convert it
        if isinstance(default_config[param], bool) and isinstance(config[param], str):
            config[param] = str_to_bool(string=config[param], name=param)

        # If the default value is an int, but we have a string, convert it
        if isinstance(default_config[param], int) and isinstance(config[param], str):
            config[param] = int(config[param])

        # Finally any 'None' string should just be None
        if default_config[param] is None and config[param] == 'None':
            config[param] = None

        # Ensure model model is supported
        if config['modem_model'] not in modems_supported:
            raise RuntimeError('Model model %s not supported!' % config['modem_model'])

    # This gets the correct function to use to parse the modem's html based on model
    # If you're adding new modems and get an error about no module, create src/arris_stats_yourmodel.py
    module = __import__('arris_stats_' + config['modem_model'])
    config['parse_html_function'] = getattr(module, 'parse_html_' + config['modem_model'])
    try:
        config['get_token_function'] = getattr(module, 'get_token_' + config['modem_model'])
    except AttributeError:
        config['get_token_function'] = None
    return config


def get_token(config, session):
    """ Get the auth token by sending the
        username and password pair for basic auth. They
        also want the pair as a base64 encoded get req param
    """
    logging.info('Obtaining login session from modem')

    url = config['modem_url']
    username = config['modem_username']
    password = config['modem_password']
    verify_ssl = config['modem_verify_ssl']

    # We have to send a request with the username and password
    # encoded as a url param.  Look at the Javascript from the
    # login page for more info on the following.
    token = username + ":" + password
    auth_hash = base64.b64encode(token.encode('ascii')).decode()
    auth_url = url + '?login_' + auth_hash
    # logging.debug('auth_url: %s', auth_url)

    # This is going to respond with a token, which is a hash that we
    # have to send as a get parameter with subsequent requests
    # Requests will automatically handle the session cookies
    try:
        resp = session.get(auth_url, headers={'Authorization': 'Basic ' + auth_hash}, verify=verify_ssl)
        if resp.status_code != 200:
            logging.error('Error authenticating with %s', url)
            logging.error('Status code: %s', resp.status_code)
            logging.error('Reason: %s', resp.reason)
            return None
        resp.close()
    except Exception as exception:
        logging.error(exception)
        logging.error('Error authenticating with %s', url)
        return None

    if 'Password:' in resp.text:
        logging.error('Authentication error, received login page.  Check username / password.  SB8200 has some kind of bug that can cause this after too many authentications, the only known fix is to reboot the modem.')
        return None

    token = resp.text
    return token


def get_html(config, token, session):
    """ Get the status page from the modem
        return the raw html
    """

    if config['modem_auth_required']:
        url = config['modem_url'] + '?ct_' + token
    else:
        url = config['modem_url']

    verify_ssl = config['modem_verify_ssl']

    logging.info('Retreiving stats from %s', config['modem_url'])
    logging.debug('Cookies: %s', session.cookies)
    logging.debug('Full url: %s', url)

    try:
        resp = session.get(url, verify=verify_ssl)
        if resp.status_code != 200:
            logging.error('Error retreiving html from %s', url)
            logging.error('Status code: %s', resp.status_code)
            logging.error('Reason: %s', resp.reason)
            return None
        status_html = resp.content.decode("utf-8")
        resp.close()
    except Exception as exception:
        logging.error(exception)
        logging.error('Error retreiving html from %s', url)
        return None

    if 'Password:' in status_html:
        logging.error('Authentication error, received login page.  This can happen once when a new session is established and you should let it retry, but if it persists then check username / password.')
        if not config['modem_auth_required']:
            logging.warning('You have modem_auth_required to False, but a login page was detected!')
        return None

    return status_html


def error_exit(message, config=None, sleep=True):
    """ Log error, sleep if needed, then exit 1 """
    logging.error(message)
    if sleep and config and config['sleep_before_exit']:
        logging.info('Sleeping for %s seconds before exiting since sleep_before_exit is True', config['sleep_interval'])
        time.sleep(config['sleep_interval'])
    sys.exit(1)


def write_html(html):
    """ write html to file """
    with open("/tmp/html", "wb") as text_file:
        text_file.write(html)


def read_html():
    """ read html from file """
    with open("/tmp/html", "rb") as text_file:
        html = text_file.read()
    return html


def str_to_bool(string, name):
    """ Return True is string ~= 'true' """
    if string.lower() == 'true':
        return True
    if string.lower() == 'false':
        return False

    raise ValueError('Config parameter % s should be boolean "true" or "false", but value is neither of those.' % name)


def init_logger(log_level="info"):
    """ Start the python logger """
    log_format = '%(asctime)s %(levelname)-8s %(message)s'

    level = logging.INFO

    if log_level == "debug":
        level = logging.DEBUG
    elif log_level == "info":
        level = logging.INFO
    elif log_level == "warning":
        level = logging.WARNING
    elif log_level == "error":
        level = logging.ERROR

    # https://stackoverflow.com/a/61516733/866057
    try:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_handler = root_logger.handlers[0]
        root_handler.setFormatter(logging.Formatter(log_format))
    except IndexError:
        logging.basicConfig(level=level, format=log_format)


if __name__ == '__main__':
    main()
