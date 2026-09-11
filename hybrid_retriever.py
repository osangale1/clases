from dotenv import load_dotenv
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_pinecone import PineconeVectorStore

from embeddings import get_embeddings
from ingest import INDEX_NAME, NAMESPACE, cargar_y_fragmentar

load_dotenv()

TOP_K = 5


class RAGSystem:
    def __init__(self):
        fragmentos = cargar_y_fragmentar()

        bm25 = BM25Retriever.from_documents(fragmentos)
        bm25.k = TOP_K

        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=get_embeddings(),
            namespace=NAMESPACE,
        )
        vectorial = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

        self.retriever = EnsembleRetriever(retrievers=[bm25, vectorial], weights=[0.5, 0.5])

    def buscar(self, pregunta: str):
        return self.retriever.invoke(pregunta)[:TOP_K]
