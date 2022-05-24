FROM python:3.8-alpine

ENV arris_stats_debug=False \
  destination=influxdb \
  sleep_interval=300 \
  modem_url=https://192.168.100.1/cmconnectionstatus.html \
  modem_verify_ssl=False \
  modem_auth_required=False \
  modem_username=admin \
  modem_password=None \
  modem_model=sb8200 \
  exit_on_auth_error=True \
  exit_on_html_error=True \
  clear_auth_token_on_html_error=True \
  sleep_before_exit=True \
  \
  # Influx All versions
  influx_major_version=1 \
  influx_verify_ssl=True \
  \
  # Influx 1.x settings
  influx_host=localhost \
  influx_database=cable_modem_stats \
  influx_port=8086 \
  influx_username=None \
  influx_password=None \
  influx_use_ssl=False \
  \
  # Influx 2.x settings
  influx_org=None \
  influx_url=http://localhost:8086 \
  influx_bucket=cable_modem_stats \
  influx_token=None \
  \
  # AWS Timestream
  timestream_aws_access_key_id=None \
  timestream_aws_secret_access_key=None \
  timestream_database=cable_modem_stats \
  timestream_table=cable_modem_stats \
  timestream_aws_region=us-east-1 \
  \
  # Splunk
  splunk_host=None \
  splunk_token=None \
  splunk_port=8088 \
  splunk_ssl=False \
  splunk_verify_ssl=True \
  splunk_source=arris_cable_modem_stats

COPY src/requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /src

# If you want to use a config.ini, this overrides all ENV vars
# CMD ["python3","arris_stats.py","--config","config.ini"]

# This uses the ENV vars and NOT config.ini
CMD ["python3","arris_stats.py"]
