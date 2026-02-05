@echo off
REM Simple PostgreSQL backup helper (Windows)
set BACKUP_DIR=backups
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%
for /f "tokens=1-6 delims=:." %%a in ("%date% %time%") do set TS=%%a-%%b-%%c_%%d-%%e-%%f













echo Backup saved to %BACKUP_DIR%\backup-%TS%.dumppg_dump "%PG_URL%" -Fc -f "%BACKUP_DIR%\backup-%TS%.dump"set PG_URL=%DATABASE_URL:+asyncpg=%REM Remove +asyncpg if present)  exit /b 1  echo DATABASE_URL not set. Set it in environment or backend\.envif "%DATABASE_URL%"=="" ()  for /f "usebackq tokens=* delims=" %%G in (`type backend\.env ^| findstr /v "^#"`) do set "%%G"if exist backend\.env (nREM Load DATABASE_URL from backend\.env if present