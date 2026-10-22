Corrida REAL con Gemini (tier gratuito), ver `reports/gemini_real.md`:

- `phoenix_gemini_real_traza_rag.png`: traza de `POST /tasks` con Gemini real (`gemini-3.6-flash`):
  supervisor, investigador y herramienta RAG, con tokens reales y latencia (35 s).

Capturas de Phoenix generadas con `python -m scripts.demo_trazas_offline` (LLM con guion, sin
API keys, por eso el costo sale en `$0`):

- `phoenix_trazas_demo_offline.png`: proyecto con las 29 trazas de las 7 pruebas contra la API.
- `phoenix_traza_detalle_hitl_offline.png`: detalle de una traza de `POST /tasks/{id}/approve`
  rechazando una tarea critica (`aprobacion` -> `enrutar_aprobacion` -> `sintesis`).

Pendiente (cupo diario del tier gratis): las 7 pruebas completas con modelo real:

- costo por ejecucion y latencia p95 con tokens reales en Phoenix.

Pasos: `./run.sh`, despues `python scripts/pruebas.py`, y sacar las capturas del
dashboard de Phoenix (http://localhost:6006) o de LangSmith.
