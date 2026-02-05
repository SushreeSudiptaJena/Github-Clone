@echo off
REM Run alembic migrations (Windows)
IF "%DATABASE_URL%"=="" (
  echo DATABASE_URL not set. Create backend\.env with DATABASE_URL or set env var.
  exit /b 1
)
alembic -c backend\alembic.ini upgrade head
echo Migrations applied.
