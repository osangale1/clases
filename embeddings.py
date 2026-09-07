import os

from langchain_openai import OpenAIEmbeddings


def get_embeddings():
    """
    Un solo lugar para armar los embeddings, asi indexamos y consultamos
    siempre con el mismo modelo (si no coinciden, la busqueda por similitud
    no sirve de nada). Ademas la dimension tiene que matchear la del indice
    de Pinecone (1536 para text-embedding-3-small).
    """
    modelo = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=modelo)
