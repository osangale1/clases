import asyncio
import time

import httpx

BASE_URL = "http://localhost:8000"
PREGUNTAS = [
    "Buscame info sobre LangGraph y decime si suena positivo",
    "Buscame info sobre Redis y decime si suena positivo",
    "Buscame info sobre Pinecone y decime si suena positivo",
    "Buscame info sobre ChromaDB y decime si suena positivo",
    "Buscame info sobre LangChain y decime si suena positivo",
]


async def mandar_tarea(client: httpx.AsyncClient, texto: str) -> tuple[float, dict]:
    inicio = time.perf_counter()
    r = await client.post(f"{BASE_URL}/tasks", json={"texto": texto})
    duracion = time.perf_counter() - inicio
    return duracion, r.json()


async def main() -> None:
    async with httpx.AsyncClient() as client:
        resultados = await asyncio.gather(*[mandar_tarea(client, p) for p in PREGUNTAS])

    for duracion, data in resultados:
        print(f"{duracion:.3f}s -> {data}")


if __name__ == "__main__":
    asyncio.run(main())
