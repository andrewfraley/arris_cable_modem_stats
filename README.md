# arris_cable_modem_stats

This is a Python script to scrape stats from the Arris cable modem web interface.  Results are meant to be sent to InfluxDB for use with Grafana, but other targets could be added.  This currently only works with the Arris SB8200.  Credit goes to https://github.com/billimek/SB6183-stats-for-influxdb


![screen shot 1](readme/ss1.png)
![screen shot 2](readme/ss2.png)

## Run Locally

- Install [pipenv](https://github.com/pypa/pipenv) On a Mac with Homebrew, ```brew install pipenv```
- Install pip dependencies (from the root of this repo): ```pipenv install```
- Edit config.ini and change [INFLUXDB] host to your influxdb server
- pipenv run python3 sb8200_stats.py


### Debugging
```pipenv run python3 sb8200_stats.py  --debug```

## InfluxDB
The database will be created automatically if the user has permissions (config.ini defaults to anonymous access).  You can set the database name in config.ini using the [INFLUXDB] database parameter.

## Grafana
Import a new dashboard using the sb8200_grafana.json file.  Originally exported from Grafana v6.3.3
