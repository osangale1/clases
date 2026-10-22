# Evidencia reproducible

Todo lo de esta carpeta se genera con comandos del repo. Nada esta escrito a mano.

| Archivo | Que demuestra | Como se regenera |
| --- | --- | --- |
| `test_report.txt`, `junit.xml` | 56 tests pasando (API, grafo, HITL, RAG, herramientas, Pydantic, estandares, y 2 de integracion con Redis Stack real) | `TEST_REDIS_URL=redis://localhost:6379 ./run_tests.sh` |
| `lint_report.txt` | `ruff check` y `ruff format --check` sin errores | `ruff check . && ruff format --check .` |
| `compose_report.txt` | `docker-compose.yml` valido y sus servicios | `cp .env.example .env && docker compose config` |
| `phoenix_trazas_resumen.json` | Que Phoenix recibio trazas de 7 pruebas contra la API real: spans de supervisor, investigador, analista, aprobacion, sintesis, tools y del retriever hibrido (BM25 + vectorial) | `docker compose up -d redis phoenix` y `python -m scripts.demo_trazas_offline` |

## Alcance (lo que NO prueba)

- Los tests y el demo usan un **LLM falso con guion** y embeddings falsos: verifican la logica del
  sistema (enrutamiento, pausa humana, estado, validacion, trazas), no la calidad de un modelo real.
  Por eso en Phoenix el costo sale en `$0` y no hay tokens.
- Sin `TEST_REDIS_URL` los 2 tests de integracion se saltean solos (quedan 54 pasando y 2 skipped).
- Una corrida con modelo real (costo por ejecucion, latencia con tokens reales) requiere las API keys:
  `./run.sh` y despues `python scripts/pruebas.py`.
