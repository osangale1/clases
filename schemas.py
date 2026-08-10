from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Un mensaje del chat (rol + contenido)."""

    role: Literal["system", "user", "assistant"]
    content: str


class ModelConfig(BaseModel):
    """Configuracion del modelo, validada con Pydantic."""

    model: str
    temperature: float = Field(default=1.0, ge=0, le=2)
    max_tokens: int = Field(default=1024, gt=0)


class ModelResponse(BaseModel):
    """Respuesta unificada, sin importar el proveedor."""

    content: str
    model: str
    provider: str
    usage: Optional[dict] = None
