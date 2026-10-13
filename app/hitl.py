from langchain_core.messages import AIMessage
from langgraph.types import interrupt

PALABRAS_CRITICAS = ["critico", "produccion", "alto costo", "importante"]


def es_critico(texto: str) -> bool:
    texto = texto.lower()
    return any(p in texto for p in PALABRAS_CRITICAS)


def nodo_aprobacion(state):
    decision = interrupt({"pregunta": "Tarea marcada como critica. Aprobas que el analista continue?"})
    aprobado = str(decision).lower() in ("si", "true", "yes")
    if not aprobado:
        return {
            "next_agent": "FINISH",
            "task_completed": True,
            "aprobado": False,
            "messages": [AIMessage(content="La aprobacion humana fue rechazada, el analisis no se ejecuto.")],
        }
    return {"aprobado": True}
