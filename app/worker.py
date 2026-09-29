import json
import os

import redis.asyncio as redis
from langchain_core.messages import HumanMessage
from langgraph.types import Command

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


def _cliente():
    return redis.from_url(REDIS_URL, decode_responses=True)


async def set_estado(job_id: str, status: str, **extra) -> None:
    cliente = _cliente()
    await cliente.set(f"job:{job_id}", json.dumps({"status": status, **extra}))
    await cliente.aclose()


async def get_estado(job_id: str) -> dict | None:
    cliente = _cliente()
    data = await cliente.get(f"job:{job_id}")
    await cliente.aclose()
    return json.loads(data) if data else None


async def ejecutar_tarea(grafo, job_id: str, texto: str) -> None:
    await set_estado(job_id, "RUNNING")
    config = {"configurable": {"thread_id": job_id}, "recursion_limit": 10}

    try:
        resultado = await grafo.ainvoke(
            {"messages": [HumanMessage(content=texto)], "pasos": 0, "contribuciones": {}, "aprobado": False},
            config=config,
        )
        if resultado.get("__interrupt__"):
            pregunta = resultado["__interrupt__"][0].value
            await set_estado(job_id, "WAITING_APPROVAL", pregunta=pregunta)
        else:
            await set_estado(
                job_id,
                "DONE",
                contribuciones=resultado.get("contribuciones", {}),
                respuesta=resultado["messages"][-1].content,
            )
    except Exception as e:
        await set_estado(job_id, "FAILED", error=str(e))


async def aprobar_tarea(grafo, job_id: str, aprobado: bool) -> None:
    config = {"configurable": {"thread_id": job_id}, "recursion_limit": 10}

    try:
        resultado = await grafo.ainvoke(Command(resume="si" if aprobado else "no"), config=config)
        await set_estado(
            job_id,
            "DONE",
            contribuciones=resultado.get("contribuciones", {}),
            respuesta=resultado["messages"][-1].content,
        )
    except Exception as e:
        await set_estado(job_id, "FAILED", error=str(e))
