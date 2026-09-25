#!/bin/sh
set -eu

# A release must migrate first. This read-only check prevents an unmigrated
# instance from serving if its pre-deploy step was omitted or failed.
alembic current --check-heads

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}"
