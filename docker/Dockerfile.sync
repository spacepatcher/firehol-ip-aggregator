FROM alpine:latest as base

LABEL maintainer="contact@ilyaglotov.com"
LABEL author="@spacepatcher"
LABEL repository="https://github.com/spacepatcher/Firehol-IP-Aggregator"

COPY app/requirements.txt /app/

RUN apk update \
  && apk add git \
             python3 \
             python3-dev \
             py3-pip \
  && apk add --virtual .deps build-base \
  && pip3 install -r /app/requirements.txt \
  && apk del .deps \
  && rm -rf /root/.cache/pip \
  && rm -rf /var/cache/apk

FROM base

COPY app /app

RUN adduser -D app \
  && chown -R app /app

USER app

WORKDIR /app

ENTRYPOINT ["python3", "/app/sync.py"]
