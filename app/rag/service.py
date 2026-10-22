import asyncio

from langchain_core.vectorstores import InMemoryVectorStore

from app import config
from app.rag.documentos import cargar_y_fragmentar
from app.rag.embeddings import get_embeddings
from app.rag.retriever import construir_retriever, crear_vectorstore
from app.schemas import FragmentoDoc


class RAGService:
    def __init__(self, retriever):
        self.retriever = retriever

    @classmethod
    async def crear(cls) -> "RAGService":
        fragmentos = await asyncio.to_thread(cargar_y_fragmentar)

        if config.VECTOR_STORE == "memory":
            # sin Pinecone: se indexa en memoria al arrancar (mismos embeddings, mismo retriever hibrido)
            vectorstore = InMemoryVectorStore(get_embeddings())
            await vectorstore.aadd_documents(fragmentos)
        else:
            vectorstore = await asyncio.to_thread(crear_vectorstore)

        return cls(construir_retriever(fragmentos, vectorstore))

    async def buscar(self, consulta: str) -> list[FragmentoDoc]:
        docs = await self.retriever.ainvoke(consulta)
        return [
            FragmentoDoc(
                fuente=d.metadata.get("fuente", "desconocido"),
                pagina=d.metadata.get("pagina", 1),
                categoria=d.metadata.get("categoria", "general"),
                texto=d.page_content,
            )
            for d in docs[: config.TOP_K]
        ]


_servicio: RAGService | None = None


def set_servicio(servicio: RAGService | None) -> None:
    global _servicio
    _servicio = servicio


def get_servicio() -> RAGService:
    if _servicio is None:
        raise RuntimeError("el servicio RAG no fue inicializado")
    return _servicio
