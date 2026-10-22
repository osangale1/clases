from collections import deque

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

from app.schemas import DecisionSupervisor, RespuestaFinal

# guion de respuestas del LLM falso: cada llamada saca la siguiente de la cola
COLA: deque = deque()
# (tipo, cantidad de mensajes, tipo del ultimo mensaje) de cada llamada
VISTO: list = []
# llamadas que terminaron en un mensaje del asistente (prefill, no permitido en Claude nuevos)
ERRORES_PREFILL: list = []


def reset() -> None:
    COLA.clear()
    VISTO.clear()
    ERRORES_PREFILL.clear()


def _registrar(tipo: str, mensajes: list) -> None:
    VISTO.append((tipo, len(mensajes), mensajes[-1].type))
    if mensajes[-1].type == "ai":
        ERRORES_PREFILL.append((tipo, mensajes[-1].content))


class FakeLLM(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        _registrar("msg", messages)
        tipo, valor = COLA.popleft()
        assert tipo == "msg", f"se esperaba 'msg' y el guion tenia {tipo}"
        return ChatResult(generations=[ChatGeneration(message=valor)])

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        def pop(mensajes):
            _registrar("struct", mensajes)
            tipo, valor = COLA.popleft()
            assert tipo == "struct", f"se esperaba 'struct' y el guion tenia {tipo}"
            return valor

        return RunnableLambda(pop)


def decide(siguiente: str):
    return ("struct", DecisionSupervisor(siguiente=siguiente, motivo=f"motivo {siguiente}"))


def tool_call(nombre: str, args: dict, id_: str):
    return ("msg", AIMessage(content="", tool_calls=[{"name": nombre, "args": args, "id": id_}]))


def texto(contenido: str):
    return ("msg", AIMessage(content=contenido))


def final(respuesta: str, fuentes: list[str]):
    return ("struct", RespuestaFinal(respuesta=respuesta, fuentes=fuentes))
