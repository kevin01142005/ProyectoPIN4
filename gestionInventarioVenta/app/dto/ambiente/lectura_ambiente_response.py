from datetime import datetime
from typing import Optional

from app.dto.base import DtoBase
from app.dto.tipos import FechaHora


class LecturaAmbienteResponse(DtoBase):
    id: int
    dispositivo: str
    temperatura: float
    humedad: Optional[float]
    presion: Optional[float]
    medido: FechaHora
    alerta: Optional[str] = None


class ResumenAmbienteResponse(DtoBase):
    total: int
    temperatura_min: Optional[float]
    temperatura_max: Optional[float]
    temperatura_promedio: Optional[float]
    humedad_min: Optional[float]
    humedad_max: Optional[float]
    humedad_promedio: Optional[float]
    lecturas_con_alerta: int
    ultima: Optional[LecturaAmbienteResponse]
