"""Modelos para apertura, movimientos y cierre de caja."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_model import Usuario


class CajaSesion(Base):
    __tablename__ = "caja_sesiones"
    __table_args__ = (
        CheckConstraint("estado IN ('ABIERTA','CERRADA')", name="ck_caja_sesion_estado"),
        CheckConstraint("monto_apertura >= 0", name="ck_caja_apertura_no_negativa"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_apertura_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    usuario_cierre_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    fecha_apertura: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monto_apertura: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_cierre_declarado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monto_cierre_calculado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    diferencia: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTA")
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    usuario_apertura: Mapped["Usuario"] = relationship(foreign_keys=[usuario_apertura_id])
    usuario_cierre: Mapped["Usuario | None"] = relationship(foreign_keys=[usuario_cierre_id])
    movimientos: Mapped[list["CajaMovimiento"]] = relationship(back_populates="sesion", cascade="all, delete-orphan")


class CajaMovimiento(Base):
    __tablename__ = "caja_movimientos"
    __table_args__ = (
        CheckConstraint("tipo IN ('INGRESO','EGRESO')", name="ck_caja_movimiento_tipo"),
        CheckConstraint("monto > 0", name="ck_caja_movimiento_monto_positivo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caja_sesion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("caja_sesiones.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    concepto: Mapped[str] = mapped_column(String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(150), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sesion: Mapped["CajaSesion"] = relationship(back_populates="movimientos")
    usuario: Mapped["Usuario"] = relationship()
