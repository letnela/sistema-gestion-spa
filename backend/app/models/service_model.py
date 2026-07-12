"""Modelos de las tablas `categorias_servicio` y `servicios`."""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.appointment_model import CitaServicio
    from app.models.employee_model import EmpleadoServicio
    from app.models.promotion_model import PromocionServicio


class CategoriaServicio(Base, TimestampMixin):
    """Agrupa los servicios del salón en categorías (ej. Cabello, Uñas, Spa)."""

    __tablename__ = "categorias_servicio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    servicios: Mapped[list["Servicio"]] = relationship(back_populates="categoria")

    def __repr__(self) -> str:
        return f"<CategoriaServicio {self.nombre}>"


class Servicio(Base, TimestampMixin):
    """Representa un servicio ofrecido por el salón (ej. Corte de cabello)."""

    __tablename__ = "servicios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categorias_servicio.id", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    porcentaje_comision: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("10.00")
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    categoria: Mapped["CategoriaServicio"] = relationship(back_populates="servicios")
    empleados: Mapped[list["EmpleadoServicio"]] = relationship(
        back_populates="servicio", cascade="all, delete-orphan"
    )
    citas: Mapped[list["CitaServicio"]] = relationship(back_populates="servicio")
    promociones: Mapped[list["PromocionServicio"]] = relationship(back_populates="servicio")

    def __repr__(self) -> str:
        return f"<Servicio {self.nombre}>"
