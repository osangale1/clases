import asyncio
import json
import os
from pathlib import Path

import httpx

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
ESTADOS_FINALES = ("DONE", "FAILED")
# con un LLM real (y reintentos por 429/503 del tier gratis) una tarea puede tardar varios minutos
ESPERA_MAXIMA_SEGUNDOS = int(os.environ.get("PRUEBAS_ESPERA_MAXIMA", "900"))


async def esperar(client: httpx.AsyncClient, job_id: str, extra=()) -> dict:
    for _ in range(ESPERA_MAXIMA_SEGUNDOS):
        estado = (await client.get(f"{BASE_URL}/tasks/{job_id}")).json()
        if estado["status"] in ESTADOS_FINALES or estado["status"] in extra:
            return estado
        await asyncio.sleep(1)
    raise TimeoutError(f"el job {job_id} no termino")


async def crear(client: httpx.AsyncClient, texto: str, conversation_id: str | None = None) -> dict:
    r = await client.post(f"{BASE_URL}/tasks", json={"texto": texto, "conversation_id": conversation_id})
    r.raise_for_status()
    return r.json()


async def prueba_1_rag(client):
    job = await crear(client, "Que es RAG y por que ayuda a reducir alucinaciones?")
    return await esperar(client, job["job_id"])


async def prueba_2_rag_y_analisis(client):
    job = await crear(client, "Busca info sobre Redis y analiza si el texto suena positivo o negativo")
    return await esperar(client, job["job_id"])


async def prueba_3_calculo(client):
    job = await crear(
        client,
        "Calcula el costo de una llamada con 1200 tokens de entrada y 300 de salida, "
        "a 3 USD por millon de entrada y 15 USD por millon de salida",
    )
    return await esperar(client, job["job_id"])


async def prueba_4_critica_aprobada(client):
    job = await crear(client, "Es importante: busca info sobre Pinecone y analiza si suena positivo")
    estado = await esperar(client, job["job_id"], extra=("WAITING_APPROVAL",))
    if estado["status"] != "WAITING_APPROVAL":
        return estado
    await client.post(f"{BASE_URL}/tasks/{job['job_id']}/approve", json={"aprobado": True})
    return await esperar(client, job["job_id"])


async def prueba_5_critica_rechazada(client):
    job = await crear(client, "Es critico: busca info sobre LangGraph y analiza si suena positivo")
    estado = await esperar(client, job["job_id"], extra=("WAITING_APPROVAL",))
    if estado["status"] != "WAITING_APPROVAL":
        return estado
    await client.post(f"{BASE_URL}/tasks/{job['job_id']}/approve", json={"aprobado": False})
    return await esperar(client, job["job_id"])


async def prueba_6_memoria(client):
    conversacion = "conv-prueba-memoria"
    primero = await crear(client, "Que es Pinecone?", conversation_id=conversacion)
    await esperar(client, primero["job_id"])
    segundo = await crear(client, "Y que ventaja tiene combinarlo con BM25?", conversation_id=conversacion)
    return await esperar(client, segundo["job_id"])


async def prueba_7_validacion(client):
    r = await client.post(f"{BASE_URL}/tasks", json={"texto": "a"})
    return {"status_http": r.status_code, "esperado": 422}


PRUEBAS = [
    prueba_1_rag,
    prueba_2_rag_y_analisis,
    prueba_3_calculo,
    prueba_4_critica_aprobada,
    prueba_5_critica_rechazada,
    prueba_6_memoria,
    prueba_7_validacion,
]


async def main() -> None:
    resultados = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for prueba in PRUEBAS:
            print(f"== {prueba.__name__}")
            try:
                resultados[prueba.__name__] = await prueba(client)
            except Exception as e:
                resultados[prueba.__name__] = {"error": str(e)}
            print(json.dumps(resultados[prueba.__name__], ensure_ascii=False, indent=2))

    contenido = json.dumps(resultados, ensure_ascii=False, indent=2)
    await asyncio.to_thread(Path("pruebas_resultado.json").write_text, contenido, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
