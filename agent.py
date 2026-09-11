import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from tools import buscar_pedidos, buscar_detalle_ultimo_pedido

load_dotenv()

HERRAMIENTAS = [buscar_pedidos, buscar_detalle_ultimo_pedido]


def get_llm():
    proveedor = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if proveedor == "openai":
        from langchain_openai import ChatOpenAI

        modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=modelo, temperature=0)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        modelo = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
        return ChatAnthropic(model=modelo, temperature=0)

    raise ValueError(f"proveedor no soportado: {proveedor}")


def construir_grafo(checkpointer):
    llm_con_herramientas = get_llm().bind_tools(HERRAMIENTAS)

    async def nodo_agente(state: MessagesState) -> dict:
        respuesta = await llm_con_herramientas.ainvoke(state["messages"])
        return {"messages": [respuesta]}

    grafo = StateGraph(MessagesState)
    grafo.add_node("agente", nodo_agente)
    grafo.add_node("tools", ToolNode(HERRAMIENTAS))

    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition)
    grafo.add_edge("tools", "agente")

    return grafo.compile(checkpointer=checkpointer)


async def preguntar(grafo, pregunta: str, thread_id: str, recursion_limit: int = 10) -> str:
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": recursion_limit}
    resultado = await grafo.ainvoke({"messages": [HumanMessage(content=pregunta)]}, config=config)
    return resultado["messages"][-1].content


def serializar_mensajes(mensajes) -> list[dict]:
    salida = []
    for m in mensajes:
        item = {"tipo": m.type, "contenido": m.content}
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            item["tool_calls"] = [{"herramienta": tc["name"], "argumentos": tc["args"]} for tc in tool_calls]
        if m.type == "tool":
            item["herramienta"] = getattr(m, "name", None)
        salida.append(item)
    return salida
