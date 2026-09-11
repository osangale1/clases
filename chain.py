import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from schemas import EntidadesTecnicas

load_dotenv()


class RespuestaIncompletaError(Exception):
    pass


def get_model():
    proveedor = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if proveedor == "openai":
        from langchain_openai import ChatOpenAI

        modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=modelo, temperature=0)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        modelo = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
        return ChatAnthropic(model=modelo, temperature=0)

    raise ValueError(f"proveedor no soportado: {proveedor}")


PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Extrae info tecnica del texto. {instrucciones_formato}"),
        ("human", "Texto:\n\n{texto}"),
    ]
)

INSTRUCCIONES_FORMATO = (
    "Devolveme la lista de tecnologias (tecnologias), el nivel de criticidad "
    "(nivel_de_criticidad: baja, media o alta) y un resumen corto (resumen_tecnico)."
)


def revisar_respuesta(resultado):
    raw = resultado["raw"]
    parsed = resultado["parsed"]
    error = resultado["parsing_error"]

    finish_reason = raw.response_metadata.get("stop_reason") or raw.response_metadata.get("finish_reason")
    if finish_reason in ("max_tokens", "length"):
        print("se corto por tokens, reintentando")
        raise RespuestaIncompletaError("respuesta incompleta")

    if error is not None or parsed is None:
        print("json invalido, reintentando:", error)
        raise RespuestaIncompletaError(str(error))

    return parsed


modelo = get_model()
modelo_estructurado = modelo.with_structured_output(EntidadesTecnicas, include_raw=True)

cadena = PROMPT | modelo_estructurado | RunnableLambda(revisar_respuesta)
cadena_con_reintento = cadena.with_retry(
    retry_if_exception_type=(RespuestaIncompletaError,),
    stop_after_attempt=3,
)


async def process_text(texto: str) -> EntidadesTecnicas:
    print("procesando texto...")
    return await cadena_con_reintento.ainvoke({"texto": texto, "instrucciones_formato": INSTRUCCIONES_FORMATO})
