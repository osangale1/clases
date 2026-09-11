import asyncio

from chain import process_text

TEXTO_LOG_ERROR = """
[ERROR] 2026-08-20 03:14:02 api-gateway-7f9c
Timeout conectando a PostgreSQL (pool agotado, 200/200 conexiones activas).
La cache en Redis esta funcionando bien pero no alcanza a absorber toda la carga.
El servicio corre en FastAPI detras de un Nginx. Se recomienda escalar el pool
de conexiones o agregar una replica de lectura.
"""

TEXTO_AMBIGUO = "El sistema tuvo un problema ayer, no se bien que paso, algo con la base de datos."


async def main():
    r1 = await process_text(TEXTO_LOG_ERROR)
    print(r1.model_dump_json(indent=2))

    try:
        r2 = await process_text(TEXTO_AMBIGUO)
        print(r2.model_dump_json(indent=2))
    except Exception as e:
        print("fallo despues de los reintentos:", e)


if __name__ == "__main__":
    asyncio.run(main())
