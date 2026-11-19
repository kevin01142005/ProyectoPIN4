from app.dto.base import DtoBase
from app.model.estado_notificacion import EstadoNotificacion


class EnvioReporteResponse(DtoBase):
    mensaje: str
    destinatario: str
    notificacion_id: int
    estado_envio: EstadoNotificacion