"""Modelos de las tablas `ventas` y `venta_detalles`."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoVenta
from app.database.base import AuditUserMixin, Base

if TYPE_CHECKING:
    from app.models.client_model import Cliente
    from app.models.commission_model import Comision
    from app.models.payment_model import Pago
    from app.models.product_model import Producto
    from app.models.service_model import Servicio
    from app.models.user_model import Usuario


class Venta(Base, AuditUserMixin):
    """
    Representa una venta realizada en el punto de venta, la cual puede
    incluir productos, servicios, o una combinación de ambos.
    """

    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint(f"estado IN {tuple(EstadoVenta.TODOS)}", name="ck_ventas_estado_valido"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_comprobante: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True
    )
    cita_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citas.id", ondelete="SET NULL"), unique=True, nullable=True, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    impuesto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoVenta.COMPLETADA)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cliente: Mapped["Cliente | None"] = relationship(back_populates="ventas")
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    detalles: Mapped[list["VentaDetalle"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan"
    )
    pagos: Mapped[list["Pago"]] = relationship(back_populates="venta", cascade="all, delete-orphan")
    comisiones: Mapped[list["Comision"]] = relationship(back_populates="venta")

    def __repr__(self) -> str:
        return f"<Venta {self.numero_comprobante} total={self.total}>"


class VentaDetalle(Base):
    """
    Detalle de línea de una venta. Puede referenciar un producto o un
    servicio (exactamente uno de los dos, validado a nivel de servicio de aplicación).
    """

    __tablename__ = "venta_detalles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venta_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"), nullable=True
    )
    servicio_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=True
    )
    empleado_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("empleados.id", ondelete="SET NULL"), nullable=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    venta: Mapped["Venta"] = relationship(back_populates="detalles")
    producto: Mapped["Producto | None"] = relationship(back_populates="detalles_venta")
    servicio: Mapped["Servicio | None"] = relationship()

    def __repr__(self) -> str:
        return f"<VentaDetalle venta={self.venta_id} subtotal={self.subtotal}>"
