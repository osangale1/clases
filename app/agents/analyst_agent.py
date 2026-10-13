from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm
from app.schemas import CostoInput, ResultadoCosto, ResultadoSentimiento, SentimientoInput

PALABRAS_POSITIVAS = ["facil", "bueno", "mejor", "rapido", "simple", "reduce", "ayuda"]
PALABRAS_NEGATIVAS = ["dificil", "malo", "lento", "complejo", "problema", "bloquea", "falla"]


@tool(args_schema=SentimientoInput)
def analizar_sentimiento(texto: str) -> dict:
    """Analiza si un texto suena positivo, negativo o neutral contando palabras clave. Devuelve el
    sentimiento y los puntajes. Usar sobre la info que ya junto el investigador."""
    t = texto.lower()
    positivas = sum(p in t for p in PALABRAS_POSITIVAS)
    negativas = sum(p in t for p in PALABRAS_NEGATIVAS)

    if positivas > negativas:
        sentimiento = "positivo"
    elif negativas > positivas:
        sentimiento = "negativo"
    else:
        sentimiento = "neutral"

    return ResultadoSentimiento(
        sentimiento=sentimiento, puntaje_positivo=positivas, puntaje_negativo=negativas
    ).model_dump()


@tool(args_schema=CostoInput)
def calcular_costo_tokens(
    tokens_entrada: int,
    tokens_salida: int,
    precio_entrada_por_millon: float,
    precio_salida_por_millon: float,
) -> dict:
    """Calcula el costo en USD de una llamada a un LLM a partir de los tokens de entrada y salida y del
    precio por millon de tokens de cada tipo. Usar cuando pidan estimar costos."""
    costo = (
        tokens_entrada * precio_entrada_por_millon + tokens_salida * precio_salida_por_millon
    ) / 1_000_000
    return ResultadoCosto(costo_usd=round(costo, 6)).model_dump()


def crear_agente_analista():
    return create_react_agent(
        get_llm(),
        tools=[analizar_sentimiento, calcular_costo_tokens],
        prompt=(
            "Sos el analista del equipo. Procesa la info que ya junto el investigador usando tus "
            "herramientas (sentimiento o calculo de costos) y explica el resultado. No inventes datos."
        ),
    )
