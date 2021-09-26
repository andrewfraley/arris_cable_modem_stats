FROM python:3.8-alpine

ADD src/ /src
WORKDIR /src

RUN pip install -r requirements.txt

CMD ["python3","arris_stats.py","--config","config.ini"]
