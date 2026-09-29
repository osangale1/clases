from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm

DOCS_SIMULADOS = {
    "langchain": "LangChain es un framework para armar apps con LLMs, con chains y agents.",
    "langgraph": "LangGraph agrega grafos de estado y ciclos sobre LangChain, para agentes con memoria.",
    "pinecone": "Pinecone es una base de datos vectorial serverless para busqueda semantica.",
    "chromadb": "ChromaDB es una base vectorial local, facil de correr sin infra propia.",
    "redis": "Redis es una base de datos en memoria, se usa aca para guardar el estado de los jobs.",
}


@tool
def buscar_info(tema: str) -> str:
    """Busca informacion sobre un tema tecnico (simulacion de busqueda sobre docs de pre-entregas anteriores)."""
    tema = tema.lower()
    for clave, texto in DOCS_SIMULADOS.items():
        if clave in tema:
            return texto
    return "no encontre info sobre ese tema"


def crear_agente_investigador():
    return create_react_agent(
        get_llm(),
        tools=[buscar_info],
        prompt="Sos el investigador del equipo. Usa buscar_info para conseguir datos, no inventes nada.",
    )
