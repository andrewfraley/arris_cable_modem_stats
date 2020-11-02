FROM python:3.8.5-alpine

ADD script/ /src
WORKDIR /src

RUN pip install -r requirements.txt

CMD python3 arris_stats.py
