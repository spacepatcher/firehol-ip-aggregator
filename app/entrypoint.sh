#!/bin/sh

python3 firehol_sync.py &

echo "Starting API server"
exec hug -f api.py
