from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.base_datos import Base, CamposComunes, TipoId
from app.model.estado_notificacion import EstadoNotificacion
from app.model.tipo_notificacion import TipoNotificacion


class NotificacionCorreo(CamposComunes, Base):
    """Un correo que el sistema envió (o intentó enviar). Cada destinatario genera un registro."""

    __tablename__ = "notificaciones_correo"

    __table_args__ = (Index("ix_notificaciones_correo_creado", "creado"),)

    id: Mapped[int] = mapped_column(TipoId, primary_key=True, autoincrement=True)
    tipo: Mapped[TipoNotificacion] = mapped_column(
        Enum(TipoNotificacion, native_enum=False, length=30), nullable=False
    )
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    adjunto: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estado_envio: Mapped[EstadoNotificacion] = mapped_column(
        Enum(EstadoNotificacion, native_enum=False, length=20),
        nullable=False,
        default=EstadoNotificacion.PENDIENTE,
    )
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    enviado: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)