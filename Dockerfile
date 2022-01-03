FROM python:3.10-alpine

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
  influx_org=None \
  influx_url=http://localhost:8086 \
  influx_bucket=cable_modem_stats \
  influx_token=None \
  influx_verify_ssl=True \
  timestream_aws_access_key_id=None \
  timestream_aws_secret_access_key=None \
  timestream_database=cable_modem_stats \
  timestream_table=cable_modem_stats \
  timestream_aws_region=us-east-1

COPY src/requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /src

# If you want to use a config.ini, this overrides all ENV vars
# CMD ["python3","arris_stats.py","--config","config.ini"]

# This uses the ENV vars and NOT config.ini
CMD ["python3","arris_stats.py"]
