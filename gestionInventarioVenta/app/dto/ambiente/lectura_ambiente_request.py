from datetime import datetime
from typing import Optional

from pydantic import Field

from app.dto.base import DtoBase


class LecturaAmbienteRequest(DtoBase):
    """Lo que envía el circuito (o el simulador). 'medido' es opcional: si falta, se usa la hora del servidor."""

    dispositivo: str = Field(min_length=1, max_length=60)
    temperatura: float = Field(ge=-40, le=85)
    humedad: Optional[float] = Field(default=None, ge=0, le=100)
    presion: Optional[float] = Field(default=None, ge=300, le=1100)
    medido: Optional[datetime] = None
