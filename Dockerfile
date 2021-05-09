FROM python:3.8.5-alpine

ENV destination influxdb
ENV sleep_interval 300
ENV modem_url https://192.168.100.1/cmconnectionstatus.html
ENV modem_verify_ssl False
ENV modem_auth_required False
ENV modem_username admin
ENV modem_password None
ENV modem_model sb8200
ENV exit_on_auth_error True
ENV exit_on_html_error True
ENV clear_auth_token_on_html_error True
ENV sleep_before_exit True
ENV influx_host localhost
ENV influx_database cable_modem_stats
ENV influx_port 8086
ENV influx_username None
ENV influx_password None
ENV influx_use_ssl False
ENV influx_verify_ssl True


ADD src/ /src
WORKDIR /src

RUN pip install -r requirements.txt

CMD python3 arris_stats.py --config config.ini
