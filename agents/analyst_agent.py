from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from llm import get_llm

PALABRAS_POSITIVAS = ["facil", "bueno", "mejor", "rapido", "simple"]
PALABRAS_NEGATIVAS = ["dificil", "malo", "lento", "complejo", "problema"]


@tool
def analizar_sentimiento(texto: str) -> str:
    """Analiza si un texto suena positivo, negativo o neutral (heuristica simple por palabras clave)."""
    texto = texto.lower()
    positivas = sum(p in texto for p in PALABRAS_POSITIVAS)
    negativas = sum(p in texto for p in PALABRAS_NEGATIVAS)
    if positivas > negativas:
        return "positivo"
    if negativas > positivas:
        return "negativo"
    return "neutral"


def crear_agente_analista():
    return create_react_agent(
        get_llm(),
        tools=[analizar_sentimiento],
        prompt="Sos el analista del equipo. Usa analizar_sentimiento sobre la info que te paso el investigador.",
    )
