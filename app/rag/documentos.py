import os

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config

CATEGORIAS_POR_ARCHIVO = {
    "rag.md": "rag",
    "langgraph.md": "agentes",
    "redis.md": "infraestructura",
    "pinecone.md": "vector-db",
    "observabilidad.md": "observabilidad",
    "fastapi.md": "api",
}


def cargar_y_fragmentar() -> list[Document]:
    loader = DirectoryLoader(
        config.CARPETA_DATOS,
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documentos = loader.load()

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
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
