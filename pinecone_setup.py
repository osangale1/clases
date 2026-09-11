import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

DIMENSION = 1536
CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
REGION = os.environ.get("PINECONE_REGION", "us-east-1")


def get_pinecone_client() -> Pinecone:
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("falta PINECONE_API_KEY en el .env")
    return Pinecone(api_key=api_key)


def asegurar_indice(nombre_indice: str) -> None:
    pc = get_pinecone_client()
    nombres = [i["name"] for i in pc.list_indexes()]

    if nombre_indice in nombres:
        print("el indice ya existe")
        return

    pc.create_index(
        name=nombre_indice,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=CLOUD, region=REGION),
    )

    while not pc.describe_index(nombre_indice).status["ready"]:
        time.sleep(1)

    print("indice listo")


if __name__ == "__main__":
    asegurar_indice(os.environ.get("INDEX_NAME", "curso-rag-index"))
