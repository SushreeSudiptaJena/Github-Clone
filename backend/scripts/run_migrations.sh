#!/usr/bin/env bash
set -e
if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL not set. Copy backend/.env.example to backend/.env and set DATABASE_URL or export env var."
  exit 1
fi
alembic -c backend/alembic.ini upgrade head

echo "Migrations applied."
