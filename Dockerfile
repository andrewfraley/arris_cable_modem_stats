FROM python:3.7.1-alpine

ADD . /src
WORKDIR /src

RUN pip install -r requirements.txt

CMD python3 sb8200_stats.py
