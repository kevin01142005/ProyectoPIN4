from datetime import datetime
from typing import Optional

from sqlalchemy import select

from app.model.lectura_ambiente import LecturaAmbiente
from app.repository.repositorio_jpa import RepositorioJpa


class LecturaAmbienteRepository(RepositorioJpa[LecturaAmbiente]):
    modelo = LecturaAmbiente

    def find_desde(self, desde: datetime, limite: int) -> list[LecturaAmbiente]:
        """Las últimas 'limite' lecturas desde 'desde', devueltas de la más antigua a la más reciente."""
        consulta = (
            select(LecturaAmbiente)
            .where(LecturaAmbiente.estado.is_(True), LecturaAmbiente.medido >= desde)
            .order_by(LecturaAmbiente.medido.desc())
            .limit(limite)
        )
        return list(reversed(self.db.scalars(consulta).all()))

    def find_ultima(self) -> Optional[LecturaAmbiente]:
        consulta = (
            select(LecturaAmbiente)
            .where(LecturaAmbiente.estado.is_(True))
            .order_by(LecturaAmbiente.medido.desc(), LecturaAmbiente.id.desc())
            .limit(1)
        )
        return self.db.scalar(consulta)
