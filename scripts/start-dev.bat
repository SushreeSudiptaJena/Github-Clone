@echo off
REM Start dev environment using docker-compose on Windows
IF NOT EXIST backend\.env (
  echo Copying backend\.env.example to backend\.env (please edit values if needed)...
  copy backend\.env.example backend\.env >nul
)
docker-compose up --build
