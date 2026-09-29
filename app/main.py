import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from app.graph import construir_grafo
from app.observability import setup_observability
from app.worker import aprobar_tarea, ejecutar_tarea, get_estado, set_estado

setup_observability()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with construir_grafo() as grafo:
        app.state.grafo = grafo
        yield


app = FastAPI(lifespan=lifespan)


class TareaInput(BaseModel):
    texto: str


class AprobacionInput(BaseModel):
    aprobado: bool


@app.post("/tasks")
async def crear_tarea(datos: TareaInput, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    await set_estado(job_id, "PENDING")
    background_tasks.add_task(ejecutar_tarea, app.state.grafo, job_id, datos.texto)
    return {"job_id": job_id}


@app.get("/tasks/{job_id}")
async def estado_tarea(job_id: str):
    estado = await get_estado(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="no existe ese job_id")
    return estado


@app.post("/tasks/{job_id}/approve")
async def aprobar(job_id: str, datos: AprobacionInput, background_tasks: BackgroundTasks):
    background_tasks.add_task(aprobar_tarea, app.state.grafo, job_id, datos.aprobado)
    return {"job_id": job_id, "status": "resuming"}
