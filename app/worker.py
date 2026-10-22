import logging

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app import config
from app.jobs import JobStore
from app.schemas import EstadoTarea, RespuestaFinal

logger = logging.getLogger("sistema.worker")


def _config_grafo(job_id: str, thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.RECURSION_LIMIT,
        "run_name": "sistema-final",
        "tags": ["sistema-final"],
        "metadata": {"job_id": job_id, "thread_id": thread_id},
    }


async def _guardar_resultado(store: JobStore, job_id: str, thread_id: str, resultado: dict) -> None:
    if resultado.get("__interrupt__"):
        pregunta = resultado["__interrupt__"][0].value["pregunta"]
        logger.info("job %s esperando aprobacion humana", job_id)
        await store.guardar(
            EstadoTarea(
                job_id=job_id,
                thread_id=thread_id,
                status="WAITING_APPROVAL",
                pregunta=pregunta,
                contribuciones=resultado.get("contribuciones"),
            )
        )
        return

    logger.info("job %s terminado", job_id)
    await store.guardar(
        EstadoTarea(
            job_id=job_id,
            thread_id=thread_id,
            status="DONE",
            contribuciones=resultado.get("contribuciones"),
            resultado=RespuestaFinal(**resultado["respuesta_final"]),
        )
    )


async def _marcar_fallo(store: JobStore, job_id: str, thread_id: str, error: Exception) -> None:
    logger.exception("job %s fallo", job_id)
    await store.guardar(EstadoTarea(job_id=job_id, thread_id=thread_id, status="FAILED", error=str(error)[:500]))


async def ejecutar_tarea(grafo, store: JobStore, job_id: str, thread_id: str, texto: str) -> None:
    await store.guardar(EstadoTarea(job_id=job_id, thread_id=thread_id, status="RUNNING"))
    logger.info("job %s arranca (thread %s)", job_id, thread_id)

    try:
        resultado = await grafo.ainvoke(
            {
                "messages": [HumanMessage(content=texto)],
                "pasos": 0,
                "contribuciones": {},
                "aprobado": False,
                "respuesta_final": {},
            },
            config=_config_grafo(job_id, thread_id),
        )
        await _guardar_resultado(store, job_id, thread_id, resultado)
    except Exception as e:
        await _marcar_fallo(store, job_id, thread_id, e)


async def aprobar_tarea(grafo, store: JobStore, job_id: str, thread_id: str, aprobado: bool) -> None:
    await store.guardar(EstadoTarea(job_id=job_id, thread_id=thread_id, status="RUNNING"))
    logger.info("job %s retomado (aprobado=%s)", job_id, aprobado)

    try:
        resultado = await grafo.ainvoke(
            Command(resume="si" if aprobado else "no"),
            config=_config_grafo(job_id, thread_id),
        )
        await _guardar_resultado(store, job_id, thread_id, resultado)
    except Exception as e:
        await _marcar_fallo(store, job_id, thread_id, e)
