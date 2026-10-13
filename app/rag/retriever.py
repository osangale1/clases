from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_pinecone import PineconeVectorStore

from app import config
from app.rag.embeddings import get_embeddings


def crear_vectorstore() -> PineconeVectorStore:
    return PineconeVectorStore(
        index_name=config.INDEX_NAME,
        embedding=get_embeddings(),
        namespace=config.PINECONE_NAMESPACE,
    )


def construir_retriever(fragmentos, vectorstore) -> EnsembleRetriever:
    bm25 = BM25Retriever.from_documents(fragmentos)
    bm25.k = config.TOP_K

    vectorial = vectorstore.as_retriever(search_kwargs={"k": config.TOP_K})

    return EnsembleRetriever(retrievers=[bm25, vectorial], weights=[0.5, 0.5])
