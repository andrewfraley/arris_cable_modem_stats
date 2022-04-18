"""
    Functions for model T25
    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long
import logging
from bs4 import BeautifulSoup


def follow_redirect(session, config):
    def _follow_redirect(_url):
        res = session.get(_url, verify=config['modem_verify_ssl'])
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        result = soup.find("meta", attrs={"http-equiv": "refresh"})
        if result:
            # Extract the meta refresh as T25 firmware doesn't use 403 redirects
            return _follow_redirect(
                f"{_url[:_url.rfind('/')]}/{result.attrs['content'].split(';')[1].replace('url=', '')}")
        else:
            return res.url

    return _follow_redirect(config['modem_url'])


def get_token_t25(config, session):
    logging.info('Getting login page for modem model t25')
    # a few hops to get to the login page :)
    login_url = follow_redirect(session, config)
    logging.info(f'Login page url: {login_url}')
    login_page = session.post(login_url, verify=config['modem_verify_ssl'],
                              data={'username': config['modem_username'],
                                    'password': config['modem_password']})
    login_page.raise_for_status()
    # Dummy return the token as we don't have a token for url auth (Within session)
    return "token_in_session"


def parse_html_t25(html):
    """ Parse the HTML into the modem stats dict """
    logging.info('Parsing HTML for modem model t25')

    soup = BeautifulSoup(html, 'html.parser')
    stats = {"downstream": [],
             "upstream": []
             }

    for table_row in soup.find_all("table")[0].find_all("tr"):
        if "power" in str(table_row).lower():
            continue

        if table_row.th:
            continue

        # Replace/remove "Downstream" to normalize with other models
        channel_id = table_row.find_all('td')[0].text.replace("Downstream", "").strip()

        if not channel_id.isdigit():
            continue

        # Other models supply HZ not MHZ * 1000000 to have the same stuctures as the other ones
        frequency = str(float(table_row.find_all('td')[2].text.replace(" MHz", "").strip()) * 1000000)
        power = table_row.find_all('td')[3].text.replace(" dBmV", "").strip()
        snr = table_row.find_all('td')[4].text.replace(" dB", "").strip()
        corrected = table_row.find_all('td')[7].text.strip()
        uncorrectables = table_row.find_all('td')[8].text.strip()

        stats['downstream'].append({
            'channel_id': channel_id,
            'frequency': frequency,
            'power': power,
            'snr': snr,
            'corrected': corrected,
            'uncorrectables': uncorrectables
        })

    logging.debug('downstream stats: %s', stats['downstream'])
    if not stats['downstream']:
        logging.error(
            'Failed to get any downstream stats! If you have selected the correct modem, then this could be a parsing issue in %s',
            __file__)

    # upstream table
    for table_row in soup.find_all("table")[4].find_all("tr"):
        if table_row.th:
            continue

        # Replace/remove "Upstream" to normalize with other models
        channel_id = table_row.find_all('td')[0].text.replace("Upstream", "").strip()
        if not channel_id.isdigit():
            continue

        symbol_rate = table_row.find_all('td')[5].text.replace(" kSym/s", "").strip()
        frequency = table_row.find_all('td')[2].text.replace(" MHz", "").strip()
        power = table_row.find_all('td')[3].text.replace(" dBmV", "").strip()

        stats['upstream'].append({
            'channel_id': channel_id,
            'symbol_rate': symbol_rate,
            'frequency': frequency,
            'power': power,
        })

    logging.debug('upstream stats: %s', stats['upstream'])
    if len(stats['upstream']) == 0:
        logging.error('Failed to get any upstream stats! Probably a parsing issue in parse_html_sb8200()')

    return stats
