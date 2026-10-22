import asyncio
import socket
import time
from contextlib import asynccontextmanager

import fakeredis
import httpx
import pytest
import uvicorn
from langgraph.checkpoint.memory import InMemorySaver

import app.main as m_main
from app.graph import armar_grafo
from app.rag.service import RAGService
from app.schemas import EstadoTarea, RespuestaFinal
from tests import fakes
from tests.conftest import crear_servicio_falso
from tests.fakes import decide, final, texto, tool_call


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def api(monkeypatch):
    redis_falso = fakeredis.FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(m_main.redis, "from_url", lambda *a, **k: redis_falso)

    @asynccontextmanager
    async def grafo_en_memoria():
        yield armar_grafo().compile(checkpointer=InMemorySaver())

    monkeypatch.setattr(m_main, "construir_grafo", grafo_en_memoria)

    async def crear_falso(cls):
        return await crear_servicio_falso()

    monkeypatch.setattr(RAGService, "crear", classmethod(crear_falso))

    puerto = puerto_libre()
    server = uvicorn.Server(uvicorn.Config(m_main.app, port=puerto, log_level="warning"))
    tarea = asyncio.create_task(server.serve())
    base = f"http://127.0.0.1:{puerto}"

    async with httpx.AsyncClient(base_url=base, timeout=10) as client:
        for _ in range(100):
            try:
                if (await client.get("/health")).status_code == 200:
                    break
            except httpx.HTTPError:
                await asyncio.sleep(0.1)
        else:
            raise RuntimeError("la API no levanto")
        yield client

    server.should_exit = True
    await tarea


async def esperar(client, job_id: str, extra=()) -> dict:
    for _ in range(100):
        estado = (await client.get(f"/tasks/{job_id}")).json()
        if estado["status"] in ("DONE", "FAILED") or estado["status"] in extra:
            return estado
        await asyncio.sleep(0.1)
    raise TimeoutError(job_id)


async def test_health(api):
    assert (await api.get("/health")).json() == {"status": "ok"}


async def test_post_tasks_no_bloquea_y_devuelve_job_id(api, monkeypatch):
    async def lenta(grafo, store, job_id, thread_id, texto_tarea):
        await asyncio.sleep(1.0)
        await store.guardar(
            EstadoTarea(job_id=job_id, thread_id=thread_id, status="DONE", resultado=RespuestaFinal(respuesta="ok"))
        )

    monkeypatch.setattr(m_main, "ejecutar_tarea", lenta)

    inicio = time.perf_counter()
    r = await api.post("/tasks", json={"texto": "tarea lenta"})
    duracion = time.perf_counter() - inicio

    assert r.status_code == 202
    assert duracion < 0.5, "el POST no puede esperar a que termine la tarea"
    job_id = r.json()["job_id"]
    assert (await api.get(f"/tasks/{job_id}")).json()["status"] == "PENDING"
    assert (await esperar(api, job_id))["status"] == "DONE"


async def test_tarea_completa_devuelve_respuesta_y_fuentes(api):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "RAG"}, "c1"),
            texto("RAG usa contexto recuperado. Fuente: rag.md"),
            decide("FINISH"),
            final("RAG reduce alucinaciones.", ["rag.md"]),
        ]
    )

    job = (await api.post("/tasks", json={"texto": "Que es RAG?"})).json()
    estado = await esperar(api, job["job_id"])

    assert estado["status"] == "DONE"
    assert estado["resultado"]["fuentes"] == ["rag.md"]
    assert list(estado["contribuciones"]) == ["investigador"]


async def test_hitl_pausa_aprueba_y_reaprobar_da_409(api):
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "Pinecone"}, "c1"),
            texto("Pinecone es una DB vectorial."),
            decide("analista"),
        ]
    )
    job = (await api.post("/tasks", json={"texto": "Es importante: info de Pinecone y analiza"})).json()
    pausado = await esperar(api, job["job_id"], extra=("WAITING_APPROVAL",))
    assert pausado["status"] == "WAITING_APPROVAL"
    assert pausado["pregunta"]

    fakes.COLA.extend(
        [
            tool_call("analizar_sentimiento", {"texto": "Pinecone ayuda"}, "c2"),
            texto("Positivo."),
            decide("FINISH"),
            final("Aprobado y analizado.", ["pinecone.md"]),
        ]
    )
    assert (await api.post(f"/tasks/{job['job_id']}/approve", json={"aprobado": True})).status_code == 202
    estado = await esperar(api, job["job_id"])
    assert estado["status"] == "DONE"
    assert set(estado["contribuciones"]) == {"investigador", "analista"}

    assert (await api.post(f"/tasks/{job['job_id']}/approve", json={"aprobado": True})).status_code == 409


async def test_fallo_en_background_queda_en_failed(api):
    # cola vacia: el LLM falso explota, el worker tiene que capturarlo
    job = (await api.post("/tasks", json={"texto": "esto va a fallar"})).json()
    estado = await esperar(api, job["job_id"])

    assert estado["status"] == "FAILED"
    assert estado["error"]


async def test_validacion_pydantic_y_errores_http(api):
    assert (await api.post("/tasks", json={"texto": "a"})).status_code == 422
    assert (await api.post("/tasks", json={})).status_code == 422
    assert (await api.get("/tasks/no-existe")).status_code == 404
    assert (await api.post("/tasks/no-existe/approve", json={"aprobado": True})).status_code == 404
    assert (await api.post("/tasks/x/approve", json={"aprobado": "quizas"})).status_code in (404, 422)


async def test_conversation_id_se_usa_como_thread_id(api):
    fakes.COLA.extend([decide("FINISH"), final("Hola.", [])])
    job = (await api.post("/tasks", json={"texto": "hola", "conversation_id": "conv-abc"})).json()

    assert job["thread_id"] == "conv-abc"
    assert job["job_id"] != "conv-abc"
    await esperar(api, job["job_id"])


async def test_openapi_documenta_los_endpoints(api):
    paths = (await api.get("/openapi.json")).json()["paths"]
    assert {"/tasks", "/tasks/{job_id}", "/tasks/{job_id}/approve", "/health"} <= set(paths)
