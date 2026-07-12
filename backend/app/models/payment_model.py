"""Modelo de la tabla `pagos`."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoPago, MetodoPago
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.sale_model import Venta
    from app.models.user_model import Usuario


class Pago(Base):
    """
    Representa un pago (parcial o completo) asociado a una venta.
    Una venta puede tener varios pagos hasta cubrir el total.
    """

    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint(f"metodo IN {tuple(MetodoPago.TODOS)}", name="ck_pagos_metodo_valido"),
        CheckConstraint(f"estado IN {tuple(EstadoPago.TODOS)}", name="ck_pagos_estado_valido"),
        CheckConstraint("monto > 0", name="ck_pagos_monto_positivo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metodo: Mapped[str] = mapped_column(String(30), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(150), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoPago.COMPLETO)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    venta: Mapped["Venta"] = relationship(back_populates="pagos")
    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<Pago {self.metodo} monto={self.monto}>"
