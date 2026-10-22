import pytest
from pydantic import ValidationError

from app.agents.analyst_agent import analizar_sentimiento, calcular_costo_tokens
from app.agents.research_agent import buscar_en_documentos


def test_sentimiento_positivo():
    r = analizar_sentimiento.invoke({"texto": "es simple, rapido y ayuda mucho"})
    assert r["sentimiento"] == "positivo"
    assert r["puntaje_positivo"] > r["puntaje_negativo"]


def test_sentimiento_negativo():
    r = analizar_sentimiento.invoke({"texto": "es lento, complejo y bloquea todo"})
    assert r["sentimiento"] == "negativo"


def test_sentimiento_neutral():
    assert analizar_sentimiento.invoke({"texto": "la tabla tiene tres columnas"})["sentimiento"] == "neutral"


def test_costo_tokens_calculo_exacto():
    r = calcular_costo_tokens.invoke(
        {
            "tokens_entrada": 1200,
            "tokens_salida": 300,
            "precio_entrada_por_millon": 3,
            "precio_salida_por_millon": 15,
        }
    )
    assert r == {"costo_usd": 0.0081}


def test_herramienta_valida_argumentos_con_pydantic():
    with pytest.raises(ValidationError):
        calcular_costo_tokens.invoke(
            {
                "tokens_entrada": -5,
                "tokens_salida": 1,
                "precio_entrada_por_millon": 1,
                "precio_salida_por_millon": 1,
            }
        )


async def test_buscar_en_documentos_devuelve_fragmentos_con_metadatos(servicio_rag):
    resultado = await buscar_en_documentos.ainvoke({"consulta": "RediSearch checkpointer"})
    assert resultado, "tiene que devolver al menos un fragmento"
    assert {"fuente", "pagina", "categoria", "texto"} <= set(resultado[0])
    assert "redis.md" in {f["fuente"] for f in resultado}


async def test_buscar_en_documentos_valida_consulta_corta(servicio_rag):
    with pytest.raises(ValidationError):
        await buscar_en_documentos.ainvoke({"consulta": "a"})
