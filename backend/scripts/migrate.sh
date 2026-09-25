#!/bin/sh
set -eu

# Run once per release before web instances start. Never print the database URL.
exec alembic upgrade head
