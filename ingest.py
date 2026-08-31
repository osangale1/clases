import os
import sys

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embeddings import get_embeddings

load_dotenv()

CARPETA_DATOS = "data"
CARPETA_VECTORSTORE = "./vectorstore"
NOMBRE_COLECCION = "documentos_tecnicos"


def cargar_documentos():
    """Lee todos los .txt y .md de la carpeta data/."""
    documentos = []
    for patron in ("*.txt", "*.md"):
        loader = DirectoryLoader(
            CARPETA_DATOS,
            glob=patron,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        documentos.extend(loader.load())
    return documentos


def fragmentar(documentos):
    """Chunking con overlap, para no cortar ideas a la mitad entre un fragmento y el siguiente."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=500,
        chunk_overlap=50,
    )
    return splitter.split_documents(documentos)


def ya_existe_indice() -> bool:
    return os.path.isdir(CARPETA_VECTORSTORE) and len(os.listdir(CARPETA_VECTORSTORE)) > 0


def ingestar(forzar: bool = False) -> None:
    if ya_existe_indice() and not forzar:
        print(f"Ya existe un indice en {CARPETA_VECTORSTORE}, no se vuelve a indexar.")
        print("(Si cambiaste los documentos, corre: python ingest.py --forzar)")
        return

    print("Cargando documentos de data/...")
    documentos = cargar_documentos()
    print(f"{len(documentos)} documentos encontrados.")

    fragmentos = fragmentar(documentos)
    print(f"{len(fragmentos)} fragmentos generados (chunk_size=500 tokens, overlap=50).")

    Chroma.from_documents(
        documents=fragmentos,
        embedding=get_embeddings(),
        collection_name=NOMBRE_COLECCION,
        persist_directory=CARPETA_VECTORSTORE,
    )
    print(f"Listo, indice guardado en {CARPETA_VECTORSTORE}.")


if __name__ == "__main__":
    ingestar(forzar="--forzar" in sys.argv)
