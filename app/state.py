from langgraph.graph import MessagesState


class EstadoSistema(MessagesState):
    next_agent: str
    pasos: int
    contribuciones: dict
    aprobado: bool
    respuesta_final: dict
