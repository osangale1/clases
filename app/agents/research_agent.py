from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm
from app.rag.service import get_servicio
from app.schemas import BusquedaInput


@tool(args_schema=BusquedaInput)
async def buscar_en_documentos(consulta: str) -> list[dict]:
    """Busca en la base de conocimiento (RAG hibrido BM25 + vectorial sobre Pinecone) los fragmentos mas
    relevantes para la consulta. Cada fragmento trae su fuente (archivo), pagina y categoria. Usar siempre
    antes de afirmar algo tecnico. Si devuelve una lista vacia, no hay info sobre eso."""
    fragmentos = await get_servicio().buscar(consulta)
    return [f.model_dump() for f in fragmentos]


def crear_agente_investigador():
    return create_react_agent(
        get_llm(),
        tools=[buscar_en_documentos],
        prompt=(
            "Sos el investigador del equipo. Usa buscar_en_documentos para conseguir datos y responde solo "
            "con lo que encuentres, citando la fuente (archivo). Si no hay info, decilo."
        ),
    )
