import pytest
from pydantic import ValidationError

from app.schemas import (
    CostoInput,
    DecisionSupervisor,
    EstadoTarea,
    SentimientoInput,
    TareaInput,
)


def test_tarea_rechaza_texto_corto():
    with pytest.raises(ValidationError):
        TareaInput(texto="a")


def test_tarea_rechaza_texto_demasiado_largo():
    with pytest.raises(ValidationError):
        TareaInput(texto="x" * 2001)


def test_tarea_conversation_id_es_opcional():
    assert TareaInput(texto="hola mundo").conversation_id is None
    assert TareaInput(texto="hola mundo", conversation_id="abc").conversation_id == "abc"


def test_costo_rechaza_valores_negativos():
    with pytest.raises(ValidationError):
        CostoInput(
            tokens_entrada=-1,
            tokens_salida=0,
            precio_entrada_por_millon=1,
            precio_salida_por_millon=1,
        )


def test_sentimiento_rechaza_texto_vacio():
    with pytest.raises(ValidationError):
        SentimientoInput(texto="")


def test_supervisor_solo_acepta_destinos_validos():
    assert DecisionSupervisor(siguiente="FINISH", motivo="ok").siguiente == "FINISH"
    with pytest.raises(ValidationError):
        DecisionSupervisor(siguiente="otro_agente", motivo="no existe")


def test_estado_tarea_solo_acepta_status_conocidos():
    with pytest.raises(ValidationError):
        EstadoTarea(job_id="1", thread_id="1", status="EXPLOTO")
