from sqlalchemy import select

from app.model.mensaje_chat import MensajeChat
from app.repository.repositorio_jpa import RepositorioJpa


class MensajeChatRepository(RepositorioJpa[MensajeChat]):
    modelo = MensajeChat

    def find_ultimos(self, limite: int) -> list[MensajeChat]:
        """Los últimos 'limite' mensajes, devueltos del más antiguo al más reciente."""
        consulta = (
            select(MensajeChat)
            .where(MensajeChat.estado.is_(True))
            .order_by(MensajeChat.id.desc())
            .limit(limite)
        )
        return list(reversed(self.db.scalars(consulta).all()))