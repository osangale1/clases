from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class NivelCriticidad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"


class EntidadesTecnicas(BaseModel):
    tecnologias: List[str] = Field(description="lista de tecnologias mencionadas en el texto")
    nivel_de_criticidad: NivelCriticidad
    resumen_tecnico: str

    @field_validator("tecnologias")
    @classmethod
    def no_vacio(cls, valor: List[str]) -> List[str]:
        if len(valor) == 0:
            raise ValueError("no puede quedar vacia")
        return valor
