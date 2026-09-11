import asyncio
import json

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent import construir_grafo, preguntar, serializar_mensajes


async def main() -> None:
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as memoria:
        grafo = construir_grafo(memoria)
        traza = {}

        pregunta1 = (
            "Cuantos pedidos tuvo el cliente 102, cual fue el total, "
            "y cuales son los detalles de su ultimo pedido?"
        )
        r1 = await preguntar(grafo, pregunta1, thread_id="caso-1")
        print(r1)
        estado1 = await grafo.aget_state({"configurable": {"thread_id": "caso-1"}})
        traza["caso_1_multi_paso"] = serializar_mensajes(estado1.values["messages"])

        await preguntar(grafo, "Cuantos pedidos tuvo el cliente 105 y cual fue el total?", thread_id="caso-2")
        r2 = await preguntar(grafo, "Y cual fue su ultimo pedido?", thread_id="caso-2")
        print(r2)
        estado2 = await grafo.aget_state({"configurable": {"thread_id": "caso-2"}})
        traza["caso_2_memoria_entre_turnos"] = serializar_mensajes(estado2.values["messages"])

        r3 = await preguntar(grafo, "Cuantos pedidos tuvo el cliente 999?", thread_id="caso-3")
        print(r3)
        estado3 = await grafo.aget_state({"configurable": {"thread_id": "caso-3"}})
        traza["caso_3_cliente_inexistente"] = serializar_mensajes(estado3.values["messages"])

        with open("traza_ejecucion.json", "w", encoding="utf-8") as f:
            json.dump(traza, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
