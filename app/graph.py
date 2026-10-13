import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph import END, START, StateGraph

from app import config
from app.agents.analyst_agent import crear_agente_analista
from app.agents.research_agent import crear_agente_investigador
from app.hitl import es_critico, nodo_aprobacion
from app.llm import get_llm
from app.schemas import DecisionSupervisor, RespuestaFinal
from app.state import EstadoSistema

logger = logging.getLogger("sistema.grafo")

PROMPT_SUPERVISOR = (
    "Sos el supervisor de un equipo con: investigador (busca en la base de conocimiento) y analista "
    "(analiza sentimiento o calcula costos con la info ya reunida). Rubrica: "
    "1) si todavia no hay info buscada, elegi investigador. "
    "2) si el usuario pidio un analisis o calculo y todavia no se hizo, elegi analista. "
    "3) si ya hay info suficiente y lo pedido esta hecho, elegi FINISH. "
    "No repitas a un agente que ya dio un resultado util."
)

PROMPT_SINTESIS = (
    "Redacta la respuesta final para el usuario usando SOLO lo que dijeron el investigador y el analista "
    "en la conversacion. En 'fuentes' lista los archivos citados (por ejemplo rag.md). Si no hay info "
    "suficiente o se rechazo la aprobacion, explicalo."
)


def texto_de(mensaje) -> str:
    texto = mensaje.text
    return texto() if callable(texto) else texto


def ultimo_texto_usuario(state: EstadoSistema) -> str:
    for m in reversed(state["messages"]):
        if m.type == "human":
            return texto_de(m)
    return ""


@lru_cache
def get_agente_investigador():
    return crear_agente_investigador()


@lru_cache
def get_agente_analista():
    return crear_agente_analista()


async def nodo_supervisor(state: EstadoSistema) -> dict:
    pasos = state.get("pasos", 0)
    if pasos >= config.MAX_PASOS:
        logger.warning("tope de %s pasos, se corta", config.MAX_PASOS)
        return {"next_agent": "FINISH", "pasos": pasos + 1}

    decisor = get_llm().with_structured_output(DecisionSupervisor)
    decision = await decisor.ainvoke(
        [SystemMessage(content=PROMPT_SUPERVISOR)]
        + state["messages"]
        + [HumanMessage(content="Decidi quien interviene ahora (o FINISH) y explica el motivo.")]
    )
    logger.info("supervisor paso %s -> %s (%s)", pasos + 1, decision.siguiente, decision.motivo)
    return {"next_agent": decision.siguiente, "pasos": pasos + 1}


async def nodo_investigador(state: EstadoSistema) -> dict:
    resultado = await get_agente_investigador().ainvoke(
        {
            "messages": state["messages"]
            + [HumanMessage(content="Tu turno, investigador: busca en los documentos lo que falta.")]
        }
    )
    respuesta = resultado["messages"][-1]
    contribuciones = dict(state.get("contribuciones", {}))
    contribuciones["investigador"] = texto_de(respuesta)
    logger.info("investigador aporto %s caracteres", len(contribuciones["investigador"]))
    return {"messages": [respuesta], "contribuciones": contribuciones}


async def nodo_analista(state: EstadoSistema) -> dict:
    resultado = await get_agente_analista().ainvoke(
        {
            "messages": state["messages"]
            + [HumanMessage(content="Tu turno, analista: procesa la info ya reunida con tus herramientas.")]
        }
    )
    respuesta = resultado["messages"][-1]
    contribuciones = dict(state.get("contribuciones", {}))
    contribuciones["analista"] = texto_de(respuesta)
    logger.info("analista aporto %s caracteres", len(contribuciones["analista"]))
    return {"messages": [respuesta], "contribuciones": contribuciones}


async def nodo_sintesis(state: EstadoSistema) -> dict:
    sintetizador = get_llm().with_structured_output(RespuestaFinal)
    final = await sintetizador.ainvoke(
        [SystemMessage(content=PROMPT_SINTESIS)]
        + state["messages"]
        + [HumanMessage(content="Redacta la respuesta final.")]
    )
    logger.info("sintesis lista con %s fuentes", len(final.fuentes))
    return {"messages": [AIMessage(content=final.respuesta)], "respuesta_final": final.model_dump()}


def enrutar_supervisor(state: EstadoSistema) -> Literal["investigador", "analista", "aprobacion", "sintesis"]:
    destino = state.get("next_agent", "FINISH")

    if destino == "FINISH":
        return "sintesis"

    if destino == "analista" and es_critico(ultimo_texto_usuario(state)) and not state.get("aprobado"):
        return "aprobacion"

    return destino


def enrutar_aprobacion(state: EstadoSistema) -> Literal["analista", "sintesis"]:
    return "analista" if state.get("aprobado") else "sintesis"


def armar_grafo() -> StateGraph:
    grafo = StateGraph(EstadoSistema)
    grafo.add_node("supervisor", nodo_supervisor)
    grafo.add_node("investigador", nodo_investigador)
    grafo.add_node("analista", nodo_analista)
    grafo.add_node("aprobacion", nodo_aprobacion)
    grafo.add_node("sintesis", nodo_sintesis)

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", enrutar_supervisor)
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_conditional_edges("aprobacion", enrutar_aprobacion)
    grafo.add_edge("sintesis", END)
    return grafo


@asynccontextmanager
async def construir_grafo():
    async with AsyncRedisSaver.from_conn_string(config.REDIS_URL) as checkpointer:
        yield armar_grafo().compile(checkpointer=checkpointer)
