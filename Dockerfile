FROM python:3.7.1-alpine

ADD script/ /src
WORKDIR /src

RUN pip install -r requirements.txt

CMD python3 arris_stats.py
