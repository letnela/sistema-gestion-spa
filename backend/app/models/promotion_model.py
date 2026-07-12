"""Modelos de las tablas `promociones`, `promocion_servicios` y `promocion_productos`."""
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product_model import Producto
    from app.models.service_model import Servicio


class Promocion(Base, TimestampMixin):
    """Representa una promoción o descuento vigente en un rango de fechas."""

    __tablename__ = "promociones"
    __table_args__ = (
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_promociones_fechas_validas"),
        CheckConstraint("porcentaje_descuento > 0 AND porcentaje_descuento <= 100", name="ck_promociones_descuento_valido"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    porcentaje_descuento: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    servicios: Mapped[list["PromocionServicio"]] = relationship(
        back_populates="promocion", cascade="all, delete-orphan"
    )
    productos: Mapped[list["PromocionProducto"]] = relationship(
        back_populates="promocion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Promocion {self.nombre} {self.porcentaje_descuento}%>"

    def esta_vigente(self, fecha_actual: date) -> bool:
        """Determina si la promoción está vigente en la fecha indicada."""
        return self.activa and self.fecha_inicio <= fecha_actual <= self.fecha_fin


class PromocionServicio(Base):
    """Tabla de asociación entre promociones y los servicios a los que aplican."""

    __tablename__ = "promocion_servicios"
    __table_args__ = (UniqueConstraint("promocion_id", "servicio_id", name="uq_promocion_servicio"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promocion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promociones.id", ondelete="CASCADE"), nullable=False
    )
    servicio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servicios.id", ondelete="CASCADE"), nullable=False
    )

    promocion: Mapped["Promocion"] = relationship(back_populates="servicios")
    servicio: Mapped["Servicio"] = relationship(back_populates="promociones")


class PromocionProducto(Base):
    """Tabla de asociación entre promociones y los productos a los que aplican."""

    __tablename__ = "promocion_productos"
    __table_args__ = (UniqueConstraint("promocion_id", "producto_id", name="uq_promocion_producto"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promocion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promociones.id", ondelete="CASCADE"), nullable=False
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )

    promocion: Mapped["Promocion"] = relationship(back_populates="productos")
    producto: Mapped["Producto"] = relationship(back_populates="promociones")
