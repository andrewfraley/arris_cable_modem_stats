FROM python:3.7.1-alpine

RUN apk add git
RUN git clone https://github.com/andrewfraley/arris_cable_modem_stats.git src
WORKDIR /src
RUN pip install -r requirements.txt

# This is dangerous, you shoudn't trust me this much.  Use with your own source copy!
# CMD git pull && pip install -r requirements.txt && python3 sb8200_stats.py

CMD python3 sb8200_stats.py
