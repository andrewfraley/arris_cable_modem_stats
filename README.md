# arris_cable_modem_stats

This is a Python script to scrape stats from the Arris cable modem web interface.  Results are meant to be sent to InfluxDB for use with Grafana, but other targets could be added.  This currently only works with the Arris SB8200.  Credit goes to https://github.com/billimek/SB6183-stats-for-influxdb


## Authentication
In late Oct 2020, Comcast deployed firmware updates to the SB8200 which now require authenticating against the modem.  If your modem requires authentication (you get a login page when browsing to https://192.168.100.1/), then you must edit your config.ini file (or set the matching ENV variables) and set ```modem_auth_required``` to ```True```, and set ```modem_password``` appropriately.  By default, your modem's password is the last eight characters of the serial number, located on a sticker on the bottom of the modem.

There is some kind of bug (at least with Comcast's firmware) where the modem cannot handle more than ~10 sessions.  Once those sessions have been used up, it seems you must wait for them to expire or reboot the modem.  I have not been able to successfully log out of the sessions, but this script attempts to keep reusing the same session as long as it can.

## Run Locally

- Install [pipenv](https://github.com/pypa/pipenv). On a Mac with Homebrew, ```brew install pipenv```
- Install pip dependencies (run from the script directory of this repo): ```pipenv install```
- Edit config.ini and change influx_host to your influxdb server
- ```pipenv run python3 arris_stats.py --config config.ini```

## Docker
Run in a Docker container with:

    docker build -t arris_stats .
    docker run arris_stats

Note that the same parameters from config.ini can be set as ENV variables, ENV overrides config.ini.

## Config Settings
Config settings can be provided by the config.ini file, or set as ENV variables.  ENV variables override config.ini.

- arris_stats_debug = False
    - enables debug logs
- destination = influxdb
    - influxdb is the only valid option at this time
- sleep_interval = 300
- modem_url = https://192.168.100.1/cmconnectionstatus.html
- modem_verify_ssl = False
- modem_auth_required = False
- modem_username = admin
- modem_password = None
- modem_model = sb8200
    - only sb8200 is supported at this time
- exit_on_auth_error = True
    - Any auth error will cause an exit, useful when running in a Docker container to get a new session
- exit_on_html_error = True
    - Any error retrieving the html will cause an exit, mostly redundant with exit_on_auth_error
- clear_auth_token_on_html_error = True
    - This is useful if you don't want to exit, but do want to get a new session if/when getting the stats fails
- sleep_before_exit = True
    - If you want to sleep before exiting on errors, useful for Docker container when you have restart = always
- influx_host = localhost
- influx_port = 8086
- influx_database = cable_modem_stats
    - This will be created automatically if it can
- influx_username = None
- influx_password = None
- influx_use_ssl = False
- influx_verify_ssl = True


### Debugging

You can enable debug logs in three ways:

1. Use --debug when running from cli
    - ```pipenv run python3 sb8200_stats.py --debug --config config.ini```
2. Set ENV variable ```arris_stats_debug = true```
3. Set config.ini ```arris_stats_debug = true```

## InfluxDB
The database will be created automatically if the user has permissions (config.ini defaults to anonymous access).  You can set the database name in config.ini using the [INFLUXDB] database parameter.

## Grafana

There are two Grafana examples.  The first only relies on the Python script from this repo, while the second relies on [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/).

### SB8200 Dashboard

- Setup arrris_stats.py to run from somewhere (There's a Docker example below)
- Import a new dashboard using the [grafana/sb8200_grafana.json](grafana/sb8200_grafana.json) file.  Originally exported from Grafana v6.3.3

![SB8200 Dashboard 1](readme/ss1.png)
![SB8200 Dashboard 2](readme/ss2.png)

### Internet Uptime Dashboard

- Install [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) on your InfluxDB system (or on a separate server/container)
- Drop [influxdb/telegraph_internet_uptime.conf](influxdb/telegraph_internet_uptime.conf) into ```/etc/telegraf/telegraf.d/```  (customize IPs/hosts to your liking)
- Restart/reload Telegraf
- Import [grafana/internet_uptime.json](grafana/internet_uptime.json) into Grafana

![Internet Uptime](readme/internet_uptime.png)
