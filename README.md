# API de produccion con orquestador multi-agente

Pre-entrega 7. FastAPI encima del orquestador de la pre-entrega 6, con
estado en Redis, pausa humana (HITL) para tareas criticas, y trazas a
LangSmith o Phoenix.

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Necesita Redis **con RediSearch** (el checkpointer de LangGraph lo usa para
indexar). Con Docker:

```bash
docker run -p 6379:6379 redis/redis-stack-server:latest
```

(Redis normal sin el modulo de busqueda no funciona: tira `unknown command
'FT.INFO'`.)

O todo junto (Redis + API):

```bash
docker compose up
```

## Configuracion

Copiar `.env.example` a `.env`. `LLM_PROVIDER` puede ser `anthropic` u
`openai`. Para trazas, con LangSmith alcanza con completar
`LANGCHAIN_API_KEY` (no hace falta correr nada local). Si preferis Phoenix,
poner `PHOENIX_ENABLED=true` y levantarlo con
`docker run -p 6006:6006 arizephoenix/phoenix`.

## Uso

```bash
uvicorn app.main:app --reload
```

- `POST /tasks` con `{"texto": "..."}` -> devuelve `{"job_id": "..."}` sin
  bloquear (la tarea corre en background).
- `GET /tasks/{job_id}` -> estado actual: `PENDING`, `RUNNING`, `DONE`,
  `FAILED` o `WAITING_APPROVAL` (con la `pregunta` de aprobacion).
- `POST /tasks/{job_id}/approve` con `{"aprobado": true|false}` -> retoma
  la tarea pausada.

## Prueba de carga (5 peticiones concurrentes)

```bash
python scripts/prueba_carga.py
```

Manda 5 `POST /tasks` en paralelo. El costo por ejecucion y la latencia
p95 salen del dashboard de LangSmith/Phoenix, no del script (el script solo
genera la carga).

## Human-in-the-loop

Si el texto de la tarea incluye una palabra "critica" (`critico`,
`produccion`, `alto costo`, `importante`), el grafo se detiene antes de
mandarle el trabajo al analista y queda en `WAITING_APPROVAL` hasta que
alguien llame a `/approve`. El estado (incluida la pausa) se persiste en
Redis via `AsyncRedisSaver`, asi que la aprobacion puede llegar en otra
peticion HTTP totalmente distinta.

## Estructura

- `app/state.py`: estado compartido del grafo.
- `app/agents/`: investigador (`buscar_info`) y analista
  (`analizar_sentimiento`).
- `app/hitl.py`: que cuenta como "critico" + nodo de aprobacion
  (`interrupt`).
- `app/graph.py`: arma el grafo (supervisor + especialistas + aprobacion) y
  el checkpointer de Redis.
- `app/worker.py`: corre la tarea en background y actualiza el estado en
  Redis (incluido `FAILED` si algo explota).
- `app/observability.py`: LangSmith (por variables de entorno) o Phoenix.
- `app/main.py`: la API.
- `scripts/prueba_carga.py`: dispara las 5 peticiones concurrentes.

## screenshots/

Pendientes: hacen falta Redis + la API + LangSmith/Phoenix corriendo de
verdad para sacarlas (ver `screenshots/README.md`).
