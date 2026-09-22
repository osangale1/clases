from langgraph.graph import MessagesState


class EstadoOrquestador(MessagesState):
    next_agent: str
    task_completed: bool
    pasos: int
    contribuciones: dict
