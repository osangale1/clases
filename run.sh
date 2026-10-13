#!/usr/bin/env bash
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Se creo .env desde .env.example. Completa las API keys y volve a correr ./run.sh"
  exit 1
fi

docker compose up --build
