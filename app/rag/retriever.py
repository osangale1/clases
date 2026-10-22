import re
import unicodedata

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_pinecone import PineconeVectorStore

from app import config
from app.rag.embeddings import get_embeddings


def tokenizar(texto: str) -> list[str]:
    # el tokenizador por defecto de BM25 es text.split(): "RediSearch." (con punto) no matchea "redisearch"
    sin_acentos = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
    return re.findall(r"\w+", sin_acentos)


def crear_vectorstore() -> PineconeVectorStore:
    return PineconeVectorStore(
        index_name=config.INDEX_NAME,
        embedding=get_embeddings(),
        namespace=config.PINECONE_NAMESPACE,
    )


def construir_retriever(fragmentos, vectorstore) -> EnsembleRetriever:
    bm25 = BM25Retriever.from_documents(fragmentos, preprocess_func=tokenizar)
    bm25.k = config.TOP_K

    vectorial = vectorstore.as_retriever(search_kwargs={"k": config.TOP_K})

    return EnsembleRetriever(retrievers=[bm25, vectorial], weights=[0.5, 0.5])
