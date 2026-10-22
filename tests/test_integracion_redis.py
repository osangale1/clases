import os
import uuid

import pytest
import redis as redis_sync
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.types import Command

from app.graph import armar_grafo
from tests import fakes
from tests.fakes import decide, final, texto, tool_call

REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379")


def redis_stack_disponible() -> bool:
    try:
        redis_sync.Redis.from_url(REDIS_URL, socket_connect_timeout=1).execute_command("FT._LIST")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not redis_stack_disponible(),
    reason=f"hace falta Redis Stack en {REDIS_URL} (docker run -p 6379:6379 redis/redis-stack-server)",
)


def entrada(pregunta: str) -> dict:
    return {
        "messages": [HumanMessage(content=pregunta)],
        "pasos": 0,
        "contribuciones": {},
        "aprobado": False,
        "respuesta_final": {},
    }


def config_hilo(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}


async def test_pausa_hitl_se_reanuda_desde_otro_checkpointer(servicio_rag):
    """Simula un reinicio del servidor: la pausa se guarda en Redis y la retoma una conexion nueva."""
    thread_id = f"test-{uuid.uuid4()}"
    fakes.COLA.extend(
        [
            decide("investigador"),
            tool_call("buscar_en_documentos", {"consulta": "Redis"}, "c1"),
            texto("Redis guarda estado."),
            decide("analista"),
        ]
    )

    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as cp1:
        pausa = (
            await armar_grafo()
            .compile(checkpointer=cp1)
            .ainvoke(entrada("Es importante: info de Redis y analiza"), config=config_hilo(thread_id))
        )
        assert pausa["__interrupt__"]

    fakes.COLA.extend(
        [
            tool_call("analizar_sentimiento", {"texto": "Redis ayuda"}, "c2"),
            texto("Positivo."),
            decide("FINISH"),
            final("Retomado tras el reinicio.", ["redis.md"]),
        ]
    )
    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as cp2:
        r = await armar_grafo().compile(checkpointer=cp2).ainvoke(Command(resume="si"), config=config_hilo(thread_id))

    assert r["respuesta_final"]["respuesta"] == "Retomado tras el reinicio."
    assert set(r["contribuciones"]) == {"investigador", "analista"}


async def test_la_conversacion_sobrevive_a_un_reinicio(servicio_rag):
    thread_id = f"test-{uuid.uuid4()}"

    fakes.COLA.extend([decide("FINISH"), final("Primera.", [])])
    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as cp1:
        await armar_grafo().compile(checkpointer=cp1).ainvoke(entrada("hola"), config=config_hilo(thread_id))

    fakes.VISTO.clear()
    fakes.COLA.extend([decide("FINISH"), final("Segunda.", [])])
    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as cp2:
        await armar_grafo().compile(checkpointer=cp2).ainvoke(entrada("y ahora?"), config=config_hilo(thread_id))

    assert fakes.VISTO[0][1] > 3, "el segundo turno tiene que ver la historia guardada en Redis"
