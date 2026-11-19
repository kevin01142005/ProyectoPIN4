from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config.base_datos import Base, CamposComunes, TipoId


class LecturaAmbiente(CamposComunes, Base):
    """Una medición de temperatura y humedad enviada por el circuito del almacén."""

    __tablename__ = "lecturas_ambiente"

    __table_args__ = (Index("ix_lecturas_ambiente_medido", "medido"),)

    id: Mapped[int] = mapped_column(TipoId, primary_key=True, autoincrement=True)
    dispositivo: Mapped[str] = mapped_column(String(60), nullable=False)
    temperatura: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    humedad: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    presion: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2), nullable=True)
    medido: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
