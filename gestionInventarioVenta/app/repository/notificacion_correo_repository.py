from datetime import datetime
from typing import Optional

from sqlalchemy import func, select

from app.model.estado_notificacion import EstadoNotificacion
from app.model.notificacion_correo import NotificacionCorreo
from app.model.tipo_notificacion import TipoNotificacion
from app.repository.repositorio_jpa import RepositorioJpa


class NotificacionCorreoRepository(RepositorioJpa[NotificacionCorreo]):
    modelo = NotificacionCorreo

    def find_recientes(self, estado_envio: Optional[EstadoNotificacion], limite: int) -> list[NotificacionCorreo]:
        consulta = select(NotificacionCorreo)
        if estado_envio is not None:
            consulta = consulta.where(NotificacionCorreo.estado_envio == estado_envio)
        consulta = consulta.order_by(NotificacionCorreo.creado.desc(), NotificacionCorreo.id.desc()).limit(limite)
        return list(self.db.scalars(consulta).all())

    def contar_por_estado(self) -> dict[EstadoNotificacion, int]:
        consulta = select(NotificacionCorreo.estado_envio, func.count()).group_by(NotificacionCorreo.estado_envio)
        return {estado: int(total) for estado, total in self.db.execute(consulta).all()}

    def existe_reciente(self, tipo: TipoNotificacion, desde: datetime, referencia: Optional[str] = None) -> bool:
        """¿Ya se creó una notificación de este tipo desde 'desde'? Sirve para no repetir alertas."""
        consulta = select(NotificacionCorreo.id).where(NotificacionCorreo.tipo == tipo, NotificacionCorreo.creado >= desde)
        if referencia is not None:
            consulta = consulta.where(NotificacionCorreo.referencia == referencia)
        return self.db.scalar(consulta.limit(1)) is not None