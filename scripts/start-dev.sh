#!/usr/bin/env bash
# Start dev environment using docker-compose
set -e
if [ ! -f backend/.env ]; then
  echo "Copying backend/.env.example to backend/.env (please edit values if needed)..."
  cp backend/.env.example backend/.env
fi

docker-compose up --build
