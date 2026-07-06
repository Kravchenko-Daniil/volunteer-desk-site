#!/usr/bin/env bash
set -euo pipefail

if [[ "${WAIT_FOR_DATABASE:-True}" == "True" ]]; then
  python - <<'PY'
import os
import time
import psycopg2

deadline = time.monotonic() + 60
while True:
    try:
        connection = psycopg2.connect(
            dbname=os.environ['DATABASE_NAME'],
            user=os.environ['DATABASE_USER'],
            password=os.environ['DATABASE_PASSWORD'],
            host=os.environ.get('DATABASE_HOST', 'db'),
            port=os.environ.get('DATABASE_PORT', '5432'),
        )
        connection.close()
        break
    except psycopg2.OperationalError:
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
PY
fi

if [[ "${RUN_MIGRATIONS:-False}" == "True" ]]; then
  python manage.py migrate --noinput
fi

if [[ "${COLLECT_STATIC:-False}" == "True" ]]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
