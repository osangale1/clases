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

# separamos en su propio namespace, asi el dia de mañana que se agreguen
# otros tipos de datos al mismo indice, las busquedas no se mezclan
NAMESPACE = "documentacion-tecnica"

# categoria por archivo, para tener metadatos "avanzados" ademas de fuente/pagina
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
    """
    Carga los .md de data/ y los corta en chunks, agregando metadatos
    avanzados (fuente, pagina, categoria). La usan tanto ingest.py (para
    subir a Pinecone) como hybrid_retriever.py (para armar el BM25 en
    memoria), asi los dos lados quedan siempre con los mismos chunks.
    """
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
        textos = splitter.split_text(doc.page_content)
        for numero_pagina, texto in enumerate(textos, start=1):
            fragmentos.append(
                Document(
                    page_content=texto,
                    metadata={
                        "fuente": nombre_archivo,
                        "pagina": numero_pagina,
                        "categoria": categoria,
                    },
                )
            )
    return fragmentos


def ya_esta_indexado() -> bool:
    """Chequea si el namespace ya tiene vectores cargados, para no reindexar de arriba."""
    pc = get_pinecone_client()
    indice = pc.Index(INDEX_NAME)
    stats = indice.describe_index_stats()
    vectores_en_namespace = stats.get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0)
    return vectores_en_namespace > 0


def ingestar(forzar: bool = False) -> None:
    asegurar_indice(INDEX_NAME)

    if ya_esta_indexado() and not forzar:
        print(f"El namespace '{NAMESPACE}' ya tiene vectores cargados, no se vuelve a indexar.")
        print("(Si cambiaste los documentos, corre: python ingest.py --forzar)")
        return

    print("Cargando y fragmentando documentos de data/...")
    fragmentos = cargar_y_fragmentar()
    print(f"{len(fragmentos)} fragmentos generados (chunk_size=600 tokens, overlap=60).")

    # PineconeVectorStore guarda el texto original adentro de los metadatos
    # (campo "text" por defecto), asi no hace falta ir a buscarlo a otro lado
    PineconeVectorStore.from_documents(
        documents=fragmentos,
        embedding=get_embeddings(),
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
    )
    print(f"Listo: {len(fragmentos)} fragmentos subidos a Pinecone (indice={INDEX_NAME}, namespace={NAMESPACE}).")


if __name__ == "__main__":
    ingestar(forzar="--forzar" in sys.argv)
