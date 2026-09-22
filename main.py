import asyncio
import json

from langchain_core.messages import HumanMessage

from graph import construir_grafo


async def main() -> None:
    grafo = construir_grafo()

    entrada = {
        "messages": [HumanMessage(content="Buscame info sobre LangGraph y decime si suena positivo o negativo")],
        "pasos": 0,
        "contribuciones": {},
    }

    resultado = await grafo.ainvoke(entrada, config={"recursion_limit": 10})

    print("contribuciones:", resultado["contribuciones"])
    print("respuesta final:", resultado["messages"][-1].content)

    with open("trace_ejecucion.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "contribuciones": resultado["contribuciones"],
                "pasos": resultado["pasos"],
                "respuesta_final": resultado["messages"][-1].content,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    asyncio.run(main())
