import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

DIMENSION = 1536  # tiene que matchear el modelo de embeddings (text-embedding-3-small)
CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
REGION = os.environ.get("PINECONE_REGION", "us-east-1")


def get_pinecone_client() -> Pinecone:
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("Falta PINECONE_API_KEY en el .env")
    return Pinecone(api_key=api_key)


def asegurar_indice(nombre_indice: str) -> None:
    """Si el indice no existe lo crea (Serverless). Si ya existe, no toca nada."""
    pc = get_pinecone_client()
    nombres_existentes = [i["name"] for i in pc.list_indexes()]

    if nombre_indice in nombres_existentes:
        print(f"El indice '{nombre_indice}' ya existe, no se vuelve a crear.")
        return

    print(f"Creando indice Serverless '{nombre_indice}' (dim={DIMENSION}, {CLOUD}/{REGION})...")
    pc.create_index(
        name=nombre_indice,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=CLOUD, region=REGION),
    )

    # el indice tarda unos segundos en quedar listo para recibir datos
    while not pc.describe_index(nombre_indice).status["ready"]:
        time.sleep(1)

    print("Indice listo.")


if __name__ == "__main__":
    nombre = os.environ.get("INDEX_NAME", "curso-rag-index")
    asegurar_indice(nombre)
