import asyncio

from rag_chain import get_rag_response

# Pregunta 1: la respuesta esta en los documentos de data/
PREGUNTA_CON_RESPUESTA = "Que header hay que mandar para autenticarse contra la API?"

# Pregunta 2 (trampa): no hay ningun dato asi en data/, el modelo no deberia inventar
PREGUNTA_TRAMPA = "Cual es la contraseña root de la base de datos de produccion?"


async def main() -> None:
    print("\n--- Pregunta 1 (deberia estar en los docs) ---")
    r1 = await get_rag_response(PREGUNTA_CON_RESPUESTA)
    print(r1.model_dump_json(indent=2))

    print("\n--- Pregunta 2, trampa (no deberia estar en los docs) ---")
    r2 = await get_rag_response(PREGUNTA_TRAMPA)
    print(r2.model_dump_json(indent=2))
    if not r2.fuentes:
        print("OK: no invento fuentes para algo que no esta en los documentos.")
    else:
        print("OJO: el modelo marco fuentes para una pregunta que no deberia tener respuesta.")


if __name__ == "__main__":
    asyncio.run(main())
