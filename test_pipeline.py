import asyncio

from chain import process_text

TEXTO_LOG_ERROR = """
[ERROR] 2026-08-20 03:14:02 api-gateway-7f9c
Timeout conectando a PostgreSQL (pool agotado, 200/200 conexiones activas).
La cache en Redis esta funcionando bien pero no alcanza a absorber toda la carga.
El servicio corre en FastAPI detras de un Nginx. Se recomienda escalar el pool
de conexiones o agregar una replica de lectura.
"""

# Texto a proposito ambiguo/vago, para ver si el pipeline se recupera o revienta
TEXTO_AMBIGUO = "El sistema tuvo un problema ayer, no se bien que paso, algo con la base de datos."


async def main() -> None:
    print("\n--- Caso 1: log de error claro ---")
    resultado = await process_text(TEXTO_LOG_ERROR)
    print(resultado.model_dump_json(indent=2))

    print("\n--- Caso 2: texto ambiguo (prueba de estres) ---")
    try:
        resultado_ambiguo = await process_text(TEXTO_AMBIGUO)
        print(resultado_ambiguo.model_dump_json(indent=2))
    except Exception as e:
        print(f"El pipeline fallo despues de los reintentos: {e}")


if __name__ == "__main__":
    asyncio.run(main())
