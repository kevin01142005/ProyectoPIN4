from app.dto.base import DtoBase


class EstadoAsistenteResponse(DtoBase):
    configurado: bool
    modelo: str
    instruccion: str