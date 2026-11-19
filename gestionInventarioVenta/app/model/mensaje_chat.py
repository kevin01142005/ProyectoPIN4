from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.base_datos import Base, CamposComunes, TipoId


class MensajeChat(CamposComunes, Base):
    """Un mensaje enviado en la sala de chat. El campo 'creado' guarda la hora de envío."""

    __tablename__ = "mensajes_chat"

    __table_args__ = (Index("ix_mensajes_chat_creado", "creado"),)

    id: Mapped[int] = mapped_column(TipoId, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(TipoId, ForeignKey("usuarios.id"), nullable=False)
    autor: Mapped[str] = mapped_column(String(255), nullable=False)
    texto: Mapped[str] = mapped_column(String(500), nullable=False)