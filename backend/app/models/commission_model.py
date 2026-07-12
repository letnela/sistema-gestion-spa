"""Modelo de la tabla `comisiones`."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoComision, TipoComision
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.employee_model import Empleado
    from app.models.sale_model import Venta


class Comision(Base):
    """
    Representa la comisión generada para un empleado a partir de un
    servicio prestado o de la venta de un producto.
    """

    __tablename__ = "comisiones"
    __table_args__ = (
        CheckConstraint(f"tipo IN {tuple(TipoComision.TODOS)}", name="ck_comisiones_tipo_valido"),
        CheckConstraint(f"estado IN {tuple(EstadoComision.TODOS)}", name="ck_comisiones_estado_valido"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="CASCADE"), nullable=False
    )
    venta_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ventas.id", ondelete="SET NULL"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    porcentaje_aplicado: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    monto_comision: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoComision.PENDIENTE)
    periodo: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    empleado: Mapped["Empleado"] = relationship(back_populates="comisiones")
    venta: Mapped["Venta | None"] = relationship(back_populates="comisiones")

    def __repr__(self) -> str:
        return f"<Comision empleado={self.empleado_id} monto={self.monto_comision} estado={self.estado}>"
