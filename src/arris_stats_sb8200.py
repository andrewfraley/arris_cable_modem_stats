"""
    Functions for model SB8200
    https://github.com/andrewfraley/arris_cable_modem_stats
"""
# pylint: disable=line-too-long
import logging
from bs4 import BeautifulSoup


def parse_html_sb8200(html):
    """ Parse the HTML into the modem stats dict """
    logging.info('Parsing HTML for modem model sb8200')

    # As of Aug 2019 the SB8200 has a bug in its HTML
    # The tables have an extra </tr> in the table headers, we have to remove it so
    # that Beautiful Soup can parse it
    # Before: <tr><th colspan=7><strong>Upstream Bonded Channels</strong></th></tr>
    # After: <tr><th colspan=7><strong>Upstream Bonded Channels</strong></th>
    html = html.replace('Bonded Channels</strong></th></tr>', 'Bonded Channels</strong></th>', 2)

    soup = BeautifulSoup(html, 'html.parser')
    stats = {}

    # downstream table
    stats['downstream'] = []
    for table_row in soup.find_all("table")[1].find_all("tr"):
        if table_row.th:
            continue

        channel_id = table_row.find_all('td')[0].text.strip()

        # Some firmwares have a header row not already skiped by "if table_row.th", skip it if channel_id isn't an integer
        if not channel_id.isdigit():
            continue

        frequency = table_row.find_all('td')[3].text.replace(" Hz", "").strip()
        power = table_row.find_all('td')[4].text.replace(" dBmV", "").strip()
        snr = table_row.find_all('td')[5].text.replace(" dB", "").strip()
        corrected = table_row.find_all('td')[6].text.strip()
        uncorrectables = table_row.find_all('td')[7].text.strip()

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
        logging.error('Failed to get any downstream stats! If you have selected the correct modem, then this could be a parsing issue in %s', __file__)

    # upstream table
    stats['upstream'] = []
    for table_row in soup.find_all("table")[2].find_all("tr"):
        if table_row.th:
            continue

        channel_id = table_row.find_all('td')[1].text.strip()

        # Some firmwares have a header row not already skiped by "if table_row.th", skip it if channel_id isn't an integer
        if not channel_id.isdigit():
            continue

        frequency = table_row.find_all('td')[4].text.replace(" Hz", "").strip()
        power = table_row.find_all('td')[6].text.replace(" dBmV", "").strip()

        stats['upstream'].append({
            'channel_id': channel_id,
            'frequency': frequency,
            'power': power,
        })

    logging.debug('upstream stats: %s', stats['upstream'])
    if not stats['upstream']:
        logging.error('Failed to get any upstream stats! If you have selected the correct modem, then this could be a parsing issue in %s', __file__)

    return stats
