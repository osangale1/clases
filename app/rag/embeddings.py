from langchain_openai import OpenAIEmbeddings

from app import config


def get_embeddings():
    return OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
