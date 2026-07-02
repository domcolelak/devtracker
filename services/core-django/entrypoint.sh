#!/bin/sh
set -e

# APPLY MIGRATIONS ON EVERY CONTAINER START (WEB, celery-worker AND celery-beat ALL
# SHARE THIS IMAGE) SO THE SCHEMA IS ALWAYS UP TO DATE BEFORE THE PROCESS BELOW STARTS.
python manage.py migrate --noinput

exec "$@"
