from typing import Literal

from pydantic import Field

from app.dto.base import DtoBase


class TurnoConversacion(DtoBase):
    """Un mensaje anterior de la conversación (el chat lo reenvía para que el asistente recuerde el contexto)."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PreguntaRequest(DtoBase):
    pregunta: str = Field(min_length=1, max_length=1000)
    # Resumen de datos que el Angular armó con lo que la API le permitió ver a ese usuario (con nombres ya cambiados por códigos).
    contexto: str = Field(default="", max_length=12000)
    historial: list[TurnoConversacion] = Field(default_factory=list, max_length=20)