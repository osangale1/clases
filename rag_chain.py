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

TOP_K = 4


class RespuestaRAG(BaseModel):
    respuesta: str
    fuentes: List[str] = Field(default_factory=list)


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


def get_retriever():
    vectorstore = Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=get_embeddings(),
        persist_directory=CARPETA_VECTORSTORE,
    )
    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


def formatear_contexto(documentos) -> str:
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
            "Respondes solo con el CONTEXTO, no inventes nada. Si no esta la "
            "respuesta ahi, decilo. En 'fuentes' poné los archivos que usaste.\n\n"
            "{instrucciones_formato}",
        ),
        ("human", "CONTEXTO:\n{contexto}\n\nPREGUNTA:\n{pregunta}"),
    ]
).partial(instrucciones_formato=parser.get_format_instructions())

retriever = get_retriever()
llm = get_llm()

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
    print("consulta:", query)
    return await cadena_rag.ainvoke(query)
