import os
import sys

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embeddings import get_embeddings
from pinecone_setup import asegurar_indice, get_pinecone_client

load_dotenv()

CARPETA_DATOS = "data"
INDEX_NAME = os.environ.get("INDEX_NAME", "curso-rag-index")
NAMESPACE = "documentacion-tecnica"

CATEGORIAS_POR_ARCHIVO = {
    "peticiones_get_post.md": "peticiones",
    "autenticacion_headers.md": "autenticacion",
    "sesiones.md": "sesiones",
    "manejo_errores.md": "errores",
    "respuestas_json.md": "respuestas",
}


def cargar_documentos():
    loader = DirectoryLoader(
        CARPETA_DATOS,
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def cargar_y_fragmentar():
    documentos = cargar_documentos()
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=600,
        chunk_overlap=60,
    )

    fragmentos = []
    for doc in documentos:
        nombre_archivo = os.path.basename(doc.metadata["source"])
        categoria = CATEGORIAS_POR_ARCHIVO.get(nombre_archivo, "general")
        for i, texto in enumerate(splitter.split_text(doc.page_content), start=1):
            fragmentos.append(
                Document(
                    page_content=texto,
                    metadata={"fuente": nombre_archivo, "pagina": i, "categoria": categoria},
                )
            )
    return fragmentos


def ya_esta_indexado() -> bool:
    pc = get_pinecone_client()
    stats = pc.Index(INDEX_NAME).describe_index_stats()
    return stats.get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0) > 0


def ingestar(forzar: bool = False) -> None:
    asegurar_indice(INDEX_NAME)

    if ya_esta_indexado() and not forzar:
        print("ya esta indexado, no se vuelve a subir (usa --forzar)")
        return

    fragmentos = cargar_y_fragmentar()
    print(f"{len(fragmentos)} fragmentos")

    PineconeVectorStore.from_documents(
        documents=fragmentos,
        embedding=get_embeddings(),
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
    )
    print("listo")


if __name__ == "__main__":
    ingestar(forzar="--forzar" in sys.argv)
