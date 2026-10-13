import logging
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import BackgroundTasks, FastAPI, HTTPException

from app import config
from app.graph import construir_grafo
from app.jobs import JobStore
from app.observability import setup_logging, setup_observability
from app.rag.service import RAGService, set_servicio
from app.schemas import AprobacionInput, EstadoTarea, TareaCreada, TareaInput
from app.worker import aprobar_tarea, ejecutar_tarea

setup_logging()
setup_observability()
logger = logging.getLogger("sistema.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cliente = redis.from_url(config.REDIS_URL, decode_responses=True)
    app.state.redis = cliente
    app.state.store = JobStore(cliente)

    set_servicio(await RAGService.crear())

    async with construir_grafo() as grafo:
        app.state.grafo = grafo
        logger.info("sistema listo")
        yield

    set_servicio(None)
    await cliente.aclose()


app = FastAPI(
    title="Intelligence System",
    description="RAG hibrido + orquestador multi-agente con supervisor, estado en Redis, aprobacion humana y trazas.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    await app.state.redis.ping()
    return {"status": "ok"}


@app.post("/tasks", response_model=TareaCreada, status_code=202)
async def crear_tarea(datos: TareaInput, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    thread_id = datos.conversation_id or job_id

    await app.state.store.guardar(EstadoTarea(job_id=job_id, thread_id=thread_id, status="PENDING"))
    background_tasks.add_task(ejecutar_tarea, app.state.grafo, app.state.store, job_id, thread_id, datos.texto)
    return TareaCreada(job_id=job_id, thread_id=thread_id)


@app.get("/tasks/{job_id}", response_model=EstadoTarea)
async def estado_tarea(job_id: str):
    estado = await app.state.store.obtener(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="no existe ese job_id")
    return estado


@app.post("/tasks/{job_id}/approve", response_model=EstadoTarea, status_code=202)
async def aprobar(job_id: str, datos: AprobacionInput, background_tasks: BackgroundTasks):
    estado = await app.state.store.obtener(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="no existe ese job_id")
    if estado.status != "WAITING_APPROVAL":
        raise HTTPException(status_code=409, detail=f"el job esta en {estado.status}, no espera aprobacion")

    background_tasks.add_task(
        aprobar_tarea, app.state.grafo, app.state.store, job_id, estado.thread_id, datos.aprobado
    )
    return estado
