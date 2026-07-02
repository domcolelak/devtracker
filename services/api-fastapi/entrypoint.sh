#!/bin/sh
set -e

# core-django MUST HAVE ALREADY CREATED projects_project/common_user (docker-compose
# WAITS FOR core-django's HEALTHCHECK BEFORE STARTING THIS CONTAINER) SINCE THE
# tasks TABLE HAS REAL FOREIGN KEYS INTO THOSE TABLES.
alembic upgrade head

exec "$@"
