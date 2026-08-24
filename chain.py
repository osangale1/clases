import logging
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from schemas import EntidadesTecnicas

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline")


class RespuestaIncompletaError(Exception):
    """La tiramos cuando el LLM corta la respuesta o el JSON no valida bien."""


def get_model():
    """Arma el cliente de chat segun LLM_PROVIDER (mismo patron que el Modulo 1: openai | anthropic)."""
    proveedor = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if proveedor == "openai":
        from langchain_openai import ChatOpenAI

        modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=modelo, temperature=0)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        modelo = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
        return ChatAnthropic(model=modelo, temperature=0)

    raise ValueError(f"Proveedor no soportado en LLM_PROVIDER: {proveedor}")


# Prompt modular: el texto de entrada y las instrucciones de formato van como variables,
# nada de f-strings pegadas adentro del prompt.
PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Sos un asistente que extrae informacion tecnica de textos crudos "
            "(logs de error, descripciones de arquitectura, etc). "
            "De cada texto tenes que sacar {instrucciones_formato}",
        ),
        ("human", "Texto a analizar:\n\n{texto}"),
    ]
)

INSTRUCCIONES_FORMATO = (
    "una lista de tecnologias mencionadas (tecnologias), el nivel de criticidad "
    "del problema o arquitectura descrita (nivel_de_criticidad: baja, media o alta) "
    "y un resumen tecnico corto de 1 o 2 frases (resumen_tecnico)."
)


def revisar_respuesta(resultado: dict) -> EntidadesTecnicas:
    """
    Con include_raw=True el modelo nos devuelve raw + parsed + parsing_error.
    Ac fijamos si el LLM corto la respuesta por tokens (finish_reason) o si el
    JSON no parseo bien, antes de dar la respuesta por buena.
    """
    raw = resultado["raw"]
    parsed = resultado["parsed"]
    error = resultado["parsing_error"]

    finish_reason = raw.response_metadata.get("stop_reason") or raw.response_metadata.get("finish_reason")
    if finish_reason in ("max_tokens", "length"):
        logger.warning("El modelo corto la respuesta por limite de tokens (finish_reason=%s)", finish_reason)
        raise RespuestaIncompletaError(f"respuesta incompleta, finish_reason={finish_reason}")

    if error is not None or parsed is None:
        logger.warning("El JSON no valido bien, se reintenta. error=%s", error)
        raise RespuestaIncompletaError(f"JSON mal formado o incompleto: {error}")

    logger.info("Respuesta valida: %s", parsed.model_dump())
    return parsed


modelo = get_model()
modelo_estructurado = modelo.with_structured_output(EntidadesTecnicas, include_raw=True)

# LCEL: Prompt + LLM (con salida estructurada) + validacion propia
cadena = PROMPT | modelo_estructurado | RunnableLambda(revisar_respuesta)

# Reintento automatico si revisar_respuesta detecta algo incompleto o mal formado
cadena_con_reintento = cadena.with_retry(
    retry_if_exception_type=(RespuestaIncompletaError,),
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)


async def process_text(texto: str) -> EntidadesTecnicas:
    """Corre el pipeline completo sobre un texto y devuelve el objeto ya validado."""
    logger.info("Procesando texto de %d caracteres...", len(texto))
    resultado = await cadena_con_reintento.ainvoke(
        {"texto": texto, "instrucciones_formato": INSTRUCCIONES_FORMATO}
    )
    logger.info("Pipeline terminado ok.")
    return resultado
