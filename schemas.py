from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class NivelCriticidad(str, Enum):
    """Que tan grave es lo que se describe en el texto."""

    baja = "baja"
    media = "media"
    alta = "alta"


class EntidadesTecnicas(BaseModel):
    """Info tecnica que le pedimos al LLM que saque de un texto (log, descripcion de arquitectura, etc)."""

    tecnologias: List[str] = Field(
        description="Lista de tecnologias/herramientas mencionadas en el texto (ej: FastAPI, Redis, PostgreSQL)."
    )
    nivel_de_criticidad: NivelCriticidad = Field(
        description="Que tan critico es el problema o la arquitectura descrita: baja, media o alta."
    )
    resumen_tecnico: str = Field(
        description="Resumen tecnico breve, 1 o 2 frases, de lo que dice el texto."
    )

    @field_validator("tecnologias")
    @classmethod
    def no_vacio(cls, valor: List[str]) -> List[str]:
        if len(valor) == 0:
            raise ValueError("la lista de tecnologias no puede quedar vacia")
        return valor
