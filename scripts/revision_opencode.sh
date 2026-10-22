#!/usr/bin/env bash
# Revision de codigo con OpenCode (https://opencode.ai) usando Gemini (tier gratuito).
# Requiere: npm i -g opencode-ai  y  GOOGLE_API_KEY en .env
# Se adjuntan los archivos en un solo mensaje para gastar pocos pedidos (el cupo gratis es de 20 por dia por modelo).
set -e
MODELO=${1:-google/gemini-3.5-flash-lite}
export GOOGLE_GENERATIVE_AI_API_KEY="$(grep '^GOOGLE_API_KEY=' .env | cut -d= -f2-)"
ARGS=()
for f in $(ls app/*.py app/rag/*.py app/agents/*.py | grep -v __init__) tests/test_graph.py tests/test_api.py \
  tests/test_integracion_redis.py docker-compose.yml Dockerfile run.sh pyproject.toml requirements.txt .env.example \
  README.md docs/INFORME_TESTS.md reports/test_report.txt; do
  ARGS+=(-f "$f")
done
opencode run --agent plan -m "$MODELO" --title "Revision entrega final" "${ARGS[@]}" -- "$(cat docs/opencode/prompt.txt)" \
  < /dev/null > docs/opencode/revision_opencode_salida.md
