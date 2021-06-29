"""
    Functions for model SB8200
    https://github.com/andrewfraley/arris_cable_modem_stats

    This function written by https://github.com/mphuff
"""
# pylint: disable=line-too-long
# pylint: disable=pointless-string-statement
import logging
from bs4 import BeautifulSoup


def parse_html_sb6183(html):
    """ Parse the HTML into the modem stats dict """
    logging.info('Parsing HTML for modem model sb6183')

    # Page to parse: http://192.168.100.1/RgConnect.asp
    soup = BeautifulSoup(html, 'html.parser')
    stats = {}

    # downstream table
    stats['downstream'] = []
    logging.debug("Found %s tables", len(soup.find_all("table")))
    for table_row in soup.find_all("table")[2].find_all("tr"):
        if table_row.th:
            continue

        '''
        <tr>
    <td ><strong>Channel</strong></td>
    <td ><strong>Lock Status</strong></td>
    <td ><strong>Modulation</strong></td>
    <td ><strong>Channel ID</strong></td>
    <td ><strong>Frequency</strong></td>
    <td ><strong>Power</strong></td>
    <td ><strong>SNR</strong></td>
    <td ><strong>Corrected</strong></td>
    <td ><strong>Uncorrectables</strong></td>
   </tr>
        '''

        channel = table_row.find_all('td')[0].text.strip()
        logging.debug("Processing downstream channel %s", channel)
        # Some firmwares have a header row not already skiped by "if table_row.th", skip it if channel_id isn't an integer
        if not channel.isdigit():
            continue

        channel_id = table_row.find_all('td')[3].text.strip()
        frequency = table_row.find_all('td')[4].text.replace(" Hz", "").strip()
        power = table_row.find_all('td')[5].text.replace(" dBmV", "").strip()
        snr = table_row.find_all('td')[6].text.replace(" dB", "").strip()
        corrected = table_row.find_all('td')[7].text.strip()
        uncorrectables = table_row.find_all('td')[8].text.strip()

        stats['downstream'].append({
            'channel': channel,
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
    for table_row in soup.find_all("table")[3].find_all("tr"):
        if table_row.th:
            continue

        '''
        <tr>
            <td><strong>Channel</strong></td>
            <td><strong>Lock Status</strong></td>
                        <td><strong>US Channel Type</strong></td>
                        <td><strong>Channel ID</strong></td>
                        <td><strong>Symbol Rate</strong></td>
                        <td><strong>Frequency</strong></td>
                        <td><strong>Power</strong></td>
           </tr>
        '''

        # Some firmwares have a header row not already skiped by "if table_row.th", skip it if channel_id isn't an integer
        channel = table_row.find_all('td')[0].text.strip()
        if not channel.isdigit():
            continue

        channel_id = table_row.find_all('td')[3].text.strip()
        symbol_rate = table_row.find_all('td')[4].text.replace(" Ksym/sec", "").strip()
        frequency = table_row.find_all('td')[5].text.replace(" Hz", "").strip()
        power = table_row.find_all('td')[6].text.replace(" dBmV", "").strip()

        stats['upstream'].append({
            'channel_id': channel_id,
            'symbol_rate': symbol_rate,
            'frequency': frequency,
            'power': power,
        })

    logging.debug('upstream stats: %s', stats['upstream'])
    if not stats['upstream']:
        logging.error('Failed to get any upstream stats! If you have selected the correct modem, then this could be a parsing issue in %s', __file__)

    return stats
