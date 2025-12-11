#!/usr/bin/env bash
set -e

# create uploads folder
mkdir -p ${UPLOAD_FOLDER:-/app/uploads}
chown -R $(id -u):$(id -g) ${UPLOAD_FOLDER:-/app/uploads} || true

# run alembic migrations if enabled
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

# start gunicorn + eventlet
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
exec gunicorn -k eventlet -w ${GUNICORN_WORKERS} --bind 0.0.0.0:5000 "app:create_app()"
