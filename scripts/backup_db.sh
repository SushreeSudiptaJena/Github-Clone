#!/usr/bin/env bash
# Simple PostgreSQL backup helper using pg_dump
set -e
BACKUP_DIR=${BACKUP_DIR:-backups}
mkdir -p "$BACKUP_DIR"
TS=$(date -u +"%Y%m%dT%H%M%SZ")

if [ -z "$DATABASE_URL" ]; then
  if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
  fi
fi

if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL is not set. Set it in environment or backend/.env"
  exit 1
fi

# Convert asyncpg URL to psql-friendly URL
PG_URL=$(echo "$DATABASE_URL" | sed 's/+asyncpg//')

pg_dump "$PG_URL" -Fc -f "$BACKUP_DIR/backup-$TS.dump"

echo "Backup saved to $BACKUP_DIR/backup-$TS.dump"
