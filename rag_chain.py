import logging
import os
from typing import List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from pydantic import BaseModel, Field

from embeddings import get_embeddings
from ingest import CARPETA_VECTORSTORE, NOMBRE_COLECCION

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rag")

TOP_K = 4  # entre 3 y 5 fragmentos, no le pasamos "contexto infinito" al modelo


class RespuestaRAG(BaseModel):
    """Respuesta final del sistema: el texto y de que archivos salio."""

    respuesta: str = Field(description="Respuesta a la pregunta, basada solo en el contexto recuperado.")
    fuentes: List[str] = Field(
        description="Nombres de archivo del contexto realmente usados para responder. Lista vacia si no se encontro nada relevante."
    )


def get_llm():
    """Mismo patron que el resto del curso: elegis el proveedor con LLM_PROVIDER."""
    proveedor = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if proveedor == "openai":
        from langchain_openai import ChatOpenAI

        modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=modelo, temperature=0)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        modelo = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
        return ChatAnthropic(model=modelo, temperature=0)

    raise ValueError(f"Proveedor no soportado en LLM_PROVIDER: {proveedor}")


def get_retriever():
    vectorstore = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=get_embeddings(),
        persist_directory=CARPETA_VECTORSTORE,
    )
    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


def formatear_contexto(documentos) -> str:
    """Junta los fragmentos recuperados marcando de que archivo salio cada uno."""
    partes = []
    for doc in documentos:
        fuente = doc.metadata.get("source", "desconocido")
        partes.append(f"[Fuente: {fuente}]\n{doc.page_content}")
    return "\n\n".join(partes)


parser = PydanticOutputParser(pydantic_object=RespuestaRAG)

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Sos un asistente tecnico. Respondes UNICAMENTE en base al CONTEXTO que te paso, "
            "no uses conocimiento externo ni inventes nada. Si la respuesta no esta en el "
            "contexto, decilo claramente (por ejemplo: 'no tengo esa informacion en los "
            "documentos'). En 'fuentes' poné solo los nombres de archivo del contexto que "
            "realmente usaste para responder; si no usaste ninguno, dejala vacia.\n\n"
            "{instrucciones_formato}",
        ),
        ("human", "CONTEXTO:\n{contexto}\n\nPREGUNTA:\n{pregunta}"),
    ]
).partial(instrucciones_formato=parser.get_format_instructions())

retriever = get_retriever()
llm = get_llm()

# LCEL: retriever + prompt + LLM + parser a Pydantic
cadena_rag = (
    {
        "contexto": retriever | RunnableLambda(formatear_contexto),
        "pregunta": RunnablePassthrough(),
    }
    | PROMPT
    | llm
    | parser
)


async def get_rag_response(query: str) -> RespuestaRAG:
    """Busca en ChromaDB, arma el prompt con lo que encontro y le pregunta al LLM."""
    logger.info("Consulta: %s", query)
    respuesta = await cadena_rag.ainvoke(query)
    logger.info("Fuentes usadas: %s", respuesta.fuentes)
    return respuesta
