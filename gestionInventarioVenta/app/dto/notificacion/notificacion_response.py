from typing import Optional

from app.dto.base import DtoBase
from app.dto.tipos import FechaHora
from app.model.estado_notificacion import EstadoNotificacion
from app.model.tipo_notificacion import TipoNotificacion


class NotificacionResponse(DtoBase):
    id: int
    tipo: TipoNotificacion
    destinatario: str
    asunto: str
    referencia: Optional[str] = None
    adjunto: Optional[str] = None
    estado_envio: EstadoNotificacion
    intentos: int
    error: Optional[str] = None
    enviado: Optional[FechaHora] = None
    creado: FechaHora


class ResumenNotificacionesResponse(DtoBase):
    total: int
    pendientes: int
    enviadas: int
    fallidas: int