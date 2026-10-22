#!/usr/bin/env bash
# Corre toda la suite de tests (no necesita API keys ni Docker) y genera los reportes en reports/.
# Los tests de integracion con Redis Stack se saltean solos si no hay uno en TEST_REDIS_URL.
set -e

PYTHON=${PYTHON:-python3.12}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python3
fi

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
. .venv/bin/activate

pip install -q -r requirements-dev.txt

mkdir -p reports
pytest -v -rs --junitxml=reports/junit.xml | tee reports/test_report.txt
