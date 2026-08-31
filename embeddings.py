import os

from langchain_openai import OpenAIEmbeddings


def get_embeddings():
    """
    Un solo lugar para armar los embeddings, asi indexamos y consultamos
    siempre con el mismo modelo (si no coinciden, la busqueda por similitud
    no sirve de nada).
    """
    modelo = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=modelo)
