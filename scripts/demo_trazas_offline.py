"""Demo SIN API keys: corre 7 pruebas contra la API real, con Redis Stack y Phoenix reales, pero con un
LLM falso con guion y embeddings falsos (los mismos de tests/). Sirve para ver las trazas de cada nodo y
herramienta en Phoenix y para exportar un resumen de lo que Phoenix recibio.

NO reemplaza una corrida con modelo real (ahi las trazas traen tokens, costo y latencia reales).

Uso (con `docker compose up redis phoenix` corriendo):
    python -m scripts.demo_trazas_offline
"""

import asyncio
import json
import os
import socket
from collections import Counter
from pathlib import Path

os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("OPENAI_API_KEY", "sk-demo")
os.environ.setdefault("PINECONE_API_KEY", "demo")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-demo")
os.environ["PHOENIX_ENABLED"] = "true"
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
os.environ.setdefault("PHOENIX_PROJECT_NAME", "sistema-final-demo-offline")

import httpx  # noqa: E402
import uvicorn  # noqa: E402

import app.agents.analyst_agent as m_analista  # noqa: E402
import app.agents.research_agent as m_investigador  # noqa: E402
import app.graph as m_graph  # noqa: E402
from app import config  # noqa: E402
from app.rag.service import RAGService  # noqa: E402
from tests import fakes  # noqa: E402
from tests.conftest import crear_servicio_falso  # noqa: E402
from tests.fakes import decide, final, texto, tool_call  # noqa: E402

for modulo in (m_graph, m_analista, m_investigador):
    modulo.get_llm = lambda: fakes.FakeLLM()


async def crear_falso(cls):
    return await crear_servicio_falso()


RAGService.crear = classmethod(crear_falso)

from app.main import app  # noqa: E402

PHOENIX_BASE = config.PHOENIX_ENDPOINT.split("/v1/traces")[0]


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def esperar(client: httpx.AsyncClient, job_id: str, extra=()) -> dict:
    for _ in range(100):
        estado = (await client.get(f"/tasks/{job_id}")).json()
        if estado["status"] in ("DONE", "FAILED") or estado["status"] in extra:
            return estado
        await asyncio.sleep(0.2)
    raise TimeoutError(job_id)


def ronda_investigador(consulta: str, hallazgo: str, id_: str) -> list:
    return [decide("investigador"), tool_call("buscar_en_documentos", {"consulta": consulta}, id_), texto(hallazgo)]


async def correr_pruebas(client: httpx.AsyncClient) -> dict:
    resultados = {}

    fakes.COLA.extend(
        ronda_investigador("RAG", "RAG usa contexto recuperado. Fuente: rag.md", "a1")
        + [decide("FINISH"), final("RAG reduce alucinaciones.", ["rag.md"])]
    )
    job = (await client.post("/tasks", json={"texto": "Que es RAG y por que reduce alucinaciones?"})).json()
    resultados["1_rag"] = (await esperar(client, job["job_id"]))["status"]

    fakes.COLA.extend(
        ronda_investigador("Redis", "Redis guarda estado. Fuente: redis.md", "b1")
        + [
            decide("analista"),
            tool_call("analizar_sentimiento", {"texto": "Redis ayuda y es rapido"}, "b2"),
            texto("Sentimiento positivo."),
            decide("FINISH"),
            final("Redis suena positivo.", ["redis.md"]),
        ]
    )
    job = (await client.post("/tasks", json={"texto": "Info de Redis y analiza el sentimiento"})).json()
    resultados["2_rag_y_sentimiento"] = (await esperar(client, job["job_id"]))["status"]

    fakes.COLA.extend(
        [
            decide("analista"),
            tool_call(
                "calcular_costo_tokens",
                {
                    "tokens_entrada": 1200,
                    "tokens_salida": 300,
                    "precio_entrada_por_millon": 3,
                    "precio_salida_por_millon": 15,
                },
                "c1",
            ),
            texto("El costo es 0.0081 USD."),
            decide("FINISH"),
            final("El costo estimado es 0.0081 USD.", []),
        ]
    )
    job = (
        await client.post("/tasks", json={"texto": "Calcula el costo de 1200 tokens de entrada y 300 de salida"})
    ).json()
    resultados["3_calculo_costo"] = (await esperar(client, job["job_id"]))["status"]

    fakes.COLA.extend(
        ronda_investigador("Pinecone", "Pinecone es una DB vectorial.", "d1")
        + [
            decide("analista"),
            tool_call("analizar_sentimiento", {"texto": "Pinecone ayuda"}, "d2"),
            texto("Positivo."),
            decide("FINISH"),
            final("Aprobado y analizado.", ["pinecone.md"]),
        ]
    )
    job = (await client.post("/tasks", json={"texto": "Es importante: info de Pinecone y analiza"})).json()
    pausa = await esperar(client, job["job_id"], extra=("WAITING_APPROVAL",))
    await client.post(f"/tasks/{job['job_id']}/approve", json={"aprobado": True})
    resultados["4_critica_aprobada"] = [pausa["status"], (await esperar(client, job["job_id"]))["status"]]

    fakes.COLA.extend(
        ronda_investigador("LangGraph", "LangGraph arma grafos.", "e1")
        + [decide("analista"), final("Se rechazo la aprobacion.", ["langgraph.md"])]
    )
    job = (await client.post("/tasks", json={"texto": "Es critico: info de LangGraph y analiza"})).json()
    pausa = await esperar(client, job["job_id"], extra=("WAITING_APPROVAL",))
    await client.post(f"/tasks/{job['job_id']}/approve", json={"aprobado": False})
    resultados["5_critica_rechazada"] = [pausa["status"], (await esperar(client, job["job_id"]))["status"]]

    fakes.COLA.extend([decide("FINISH"), final("Pinecone es una base vectorial.", [])])
    job = (await client.post("/tasks", json={"texto": "Que es Pinecone?", "conversation_id": "demo-conv"})).json()
    await esperar(client, job["job_id"])
    fakes.COLA.extend([decide("FINISH"), final("Como te dije, es una base vectorial.", [])])
    job = (await client.post("/tasks", json={"texto": "y que mas?", "conversation_id": "demo-conv"})).json()
    resultados["6_memoria_entre_turnos"] = (await esperar(client, job["job_id"]))["status"]

    resultados["7_validacion_422"] = (await client.post("/tasks", json={"texto": "a"})).status_code
    return resultados


async def resumen_phoenix() -> dict:
    async with httpx.AsyncClient(base_url=PHOENIX_BASE, timeout=20) as phoenix:
        r = await phoenix.get(f"/v1/projects/{config.PHOENIX_PROJECT}/spans", params={"limit": 1000})
        spans = r.json()["data"]

    nombres = Counter(s["name"] for s in spans)
    return {
        "proyecto": config.PHOENIX_PROJECT,
        "aviso": "LLM con guion (sin tokens/costo reales): valida que cada nodo y herramienta quede trazado",
        "spans_totales": len(spans),
        "trazas": len({s["context"]["trace_id"] for s in spans}),
        "spans_por_nombre": dict(nombres.most_common()),
    }


async def main() -> None:
    puerto = puerto_libre()
    server = uvicorn.Server(uvicorn.Config(app, port=puerto, log_level="warning"))
    tarea = asyncio.create_task(server.serve())

    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{puerto}", timeout=20) as client:
        for _ in range(100):
            try:
                if (await client.get("/health")).status_code == 200:
                    break
            except httpx.HTTPError:
                await asyncio.sleep(0.2)
        resultados = await correr_pruebas(client)

    server.should_exit = True
    await tarea

    reporte = {"pruebas": resultados, "phoenix": await resumen_phoenix()}
    print(json.dumps(reporte, ensure_ascii=False, indent=2))

    destino = Path("reports/phoenix_trazas_resumen.json")
    destino.parent.mkdir(exist_ok=True)
    await asyncio.to_thread(destino.write_text, json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
