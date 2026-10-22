import asyncio
import os
import sys
import time

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app import config
from app.rag.documentos import cargar_y_fragmentar
from app.rag.embeddings import get_embeddings


def get_pinecone_client() -> Pinecone:
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("falta PINECONE_API_KEY")
    return Pinecone(api_key=api_key)


def asegurar_indice() -> None:
    pc = get_pinecone_client()
    nombres = [i["name"] for i in pc.list_indexes()]

    if config.INDEX_NAME in nombres:
        dimension = pc.describe_index(config.INDEX_NAME).dimension
        if dimension != config.EMBEDDING_DIMENSION:
            raise ValueError(
                f"el indice {config.INDEX_NAME} tiene dimension {dimension} pero los embeddings son de "
                f"{config.EMBEDDING_DIMENSION}: usa otro INDEX_NAME o borra el indice"
            )
        print("el indice ya existe")
        return

    pc.create_index(
        name=config.INDEX_NAME,
        dimension=config.EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
    )
    while not pc.describe_index(config.INDEX_NAME).status["ready"]:
        time.sleep(1)
    print("indice creado")


def ya_esta_indexado() -> bool:
    pc = get_pinecone_client()
    stats = pc.Index(config.INDEX_NAME).describe_index_stats()
    return stats.get("namespaces", {}).get(config.PINECONE_NAMESPACE, {}).get("vector_count", 0) > 0


async def ingestar(forzar: bool = False) -> None:
    if config.VECTOR_STORE == "memory":
        print("VECTOR_STORE=memory: no hay nada que subir, la API indexa en memoria al arrancar")
        return

    await asyncio.to_thread(asegurar_indice)

    if not forzar and await asyncio.to_thread(ya_esta_indexado):
        print("ya esta indexado, no se vuelve a subir (usa --forzar)")
        return

    fragmentos = await asyncio.to_thread(cargar_y_fragmentar)
    print(f"{len(fragmentos)} fragmentos")

    await PineconeVectorStore.afrom_documents(
        documents=fragmentos,
        embedding=get_embeddings(),
        index_name=config.INDEX_NAME,
        namespace=config.PINECONE_NAMESPACE,
    )
    print("listo")


if __name__ == "__main__":
    asyncio.run(ingestar(forzar="--forzar" in sys.argv))
