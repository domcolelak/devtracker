#!/bin/sh
set -e

# APPLY MIGRATIONS BEFORE SERVING. ONLY THE core-django WEB SERVICE RUNS THIS
# ENTRYPOINT: THE celery-worker AND celery-beat CONTAINERS SHARE THE IMAGE BUT
# OVERRIDE THE ENTRYPOINT IN docker-compose.yml, BECAUSE CONCURRENT `migrate`
# PROCESSES RACING AGAINST A FRESH DATABASE CAUSE DUPLICATE-KEY FAILURES IN
# POSTGRES (pg_type_typname_nsp_index ON django_content_type).
python manage.py migrate --noinput

exec "$@"
