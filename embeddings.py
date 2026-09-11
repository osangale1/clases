import os

from langchain_openai import OpenAIEmbeddings


def get_embeddings():
    modelo = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=modelo)
