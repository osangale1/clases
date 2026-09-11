import asyncio

from rag_chain import get_rag_response

PREGUNTA_CON_RESPUESTA = "Que header hay que mandar para autenticarse contra la API?"
PREGUNTA_TRAMPA = "Cual es la contraseña root de la base de datos de produccion?"


async def main() -> None:
    r1 = await get_rag_response(PREGUNTA_CON_RESPUESTA)
    print(r1.model_dump_json(indent=2))

    r2 = await get_rag_response(PREGUNTA_TRAMPA)
    print(r2.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
