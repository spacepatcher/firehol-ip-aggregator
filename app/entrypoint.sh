#!/bin/sh

apk add --no-cache git postgresql-dev gcc python3-dev musl-dev

cd /app
pip3 install -r requirements.txt

python3 firehol_sync.py &
echo "Started sync in background"

exec "$@"
echo "Started API server"