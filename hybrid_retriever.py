from dotenv import load_dotenv
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_pinecone import PineconeVectorStore

from embeddings import get_embeddings
from ingest import INDEX_NAME, NAMESPACE, cargar_y_fragmentar

load_dotenv()

TOP_K = 5


class RAGSystem:
    """
    Encapsula un EnsembleRetriever: mezcla busqueda lexica (BM25, buena para
    terminos tecnicos exactos) con la busqueda semantica de Pinecone (buena
    para preguntas con otras palabras pero el mismo significado).
    """

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

        self.retriever = EnsembleRetriever(
            retrievers=[bm25, vectorial],
            weights=[0.5, 0.5],
        )

    def buscar(self, pregunta: str):
        """Devuelve los top-5 documentos, combinando resultados lexicos y semanticos."""
        resultados = self.retriever.invoke(pregunta)
        return resultados[:TOP_K]
