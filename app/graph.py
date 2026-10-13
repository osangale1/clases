import os
from contextlib import asynccontextmanager
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph import StateGraph, START, END

from app.agents.analyst_agent import crear_agente_analista
from app.agents.research_agent import crear_agente_investigador
from app.hitl import es_critico, nodo_aprobacion
from app.llm import get_llm
from app.state import EstadoOrquestador

load_dotenv()

MAX_PASOS = 6

PROMPT_SUPERVISOR = (
    "Sos el supervisor de un equipo con: investigador (busca info) y analista "
    "(analiza esa info, sentimiento). Mira la conversacion y decidi quien sigue. "
    "Respondes SOLO con una palabra: investigador, analista o FINISH. "
    "FINISH solo cuando ya haya info buscada Y analizada."
)


def nodo_supervisor(state: EstadoOrquestador) -> dict:
    pasos = state.get("pasos", 0)
    if pasos >= MAX_PASOS:
        return {"next_agent": "FINISH", "task_completed": True, "pasos": pasos + 1}

    respuesta = get_llm().invoke(
        [SystemMessage(content=PROMPT_SUPERVISOR)]
        + state["messages"]
        + [HumanMessage(content="Decidi quien sigue: investigador, analista o FINISH.")]
    )
    decision = respuesta.content.strip().lower()

    if "investigador" in decision:
        siguiente = "investigador"
    elif "analista" in decision:
        siguiente = "analista"
    else:
        siguiente = "FINISH"

    return {"next_agent": siguiente, "pasos": pasos + 1, "task_completed": siguiente == "FINISH"}


def nodo_investigador(state: EstadoOrquestador) -> dict:
    resultado = crear_agente_investigador().invoke(
        {"messages": state["messages"] + [HumanMessage(content="Tu turno, investigador: busca la info que falta.")]}
    )
    contribuciones = dict(state.get("contribuciones", {}))
    contribuciones["investigador"] = resultado["messages"][-1].content
    return {"messages": [resultado["messages"][-1]], "contribuciones": contribuciones}


def nodo_analista(state: EstadoOrquestador) -> dict:
    resultado = crear_agente_analista().invoke(
        {"messages": state["messages"] + [HumanMessage(content="Tu turno, analista: procesa la info ya reunida.")]}
    )
    contribuciones = dict(state.get("contribuciones", {}))
    contribuciones["analista"] = resultado["messages"][-1].content
    return {"messages": [resultado["messages"][-1]], "contribuciones": contribuciones}


def enrutar(state: EstadoOrquestador) -> Literal["investigador", "analista", "aprobacion", "__end__"]:
    destino = state.get("next_agent", "FINISH")
    if destino == "FINISH":
        return END

    texto_original = state["messages"][0].content
    if destino == "analista" and es_critico(texto_original) and not state.get("aprobado"):
        return "aprobacion"

    return destino


def enrutar_aprobacion(state: EstadoOrquestador) -> Literal["analista", "__end__"]:
    return "analista" if state.get("aprobado") else END


@asynccontextmanager
async def construir_grafo():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")

    async with AsyncRedisSaver.from_conn_string(redis_url) as checkpointer:
        grafo = StateGraph(EstadoOrquestador)
        grafo.add_node("supervisor", nodo_supervisor)
        grafo.add_node("investigador", nodo_investigador)
        grafo.add_node("analista", nodo_analista)
        grafo.add_node("aprobacion", nodo_aprobacion)

        grafo.add_edge(START, "supervisor")
        grafo.add_conditional_edges("supervisor", enrutar)
        grafo.add_edge("investigador", "supervisor")
        grafo.add_edge("analista", "supervisor")
        grafo.add_conditional_edges("aprobacion", enrutar_aprobacion)

        yield grafo.compile(checkpointer=checkpointer)
