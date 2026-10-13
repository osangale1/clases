from typing import Literal, Optional

from pydantic import BaseModel, Field

StatusJob = Literal["PENDING", "RUNNING", "WAITING_APPROVAL", "DONE", "FAILED"]


# ---- API ----
class TareaInput(BaseModel):
    texto: str = Field(min_length=3, max_length=2000)
    conversation_id: Optional[str] = Field(default=None, min_length=1, max_length=100)


class TareaCreada(BaseModel):
    job_id: str
    thread_id: str


class AprobacionInput(BaseModel):
    aprobado: bool


class RespuestaFinal(BaseModel):
    respuesta: str
    fuentes: list[str] = Field(default_factory=list)


class EstadoTarea(BaseModel):
    job_id: str
    thread_id: str
    status: StatusJob
    pregunta: Optional[str] = None
    contribuciones: Optional[dict[str, str]] = None
    resultado: Optional[RespuestaFinal] = None
    error: Optional[str] = None


# ---- supervisor ----
class DecisionSupervisor(BaseModel):
    siguiente: Literal["investigador", "analista", "FINISH"]
    motivo: str


# ---- herramientas ----
class BusquedaInput(BaseModel):
    consulta: str = Field(min_length=3, max_length=500)


class FragmentoDoc(BaseModel):
    fuente: str
    pagina: int
    categoria: str
    texto: str


class SentimientoInput(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)


class ResultadoSentimiento(BaseModel):
    sentimiento: Literal["positivo", "negativo", "neutral"]
    puntaje_positivo: int
    puntaje_negativo: int


class CostoInput(BaseModel):
    tokens_entrada: int = Field(ge=0)
    tokens_salida: int = Field(ge=0)
    precio_entrada_por_millon: float = Field(ge=0)
    precio_salida_por_millon: float = Field(ge=0)


class ResultadoCosto(BaseModel):
    costo_usd: float
