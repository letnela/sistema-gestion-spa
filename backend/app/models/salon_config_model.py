"""Modelo de la tabla `configuracion_salon`."""
import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ConfiguracionSalon(Base, TimestampMixin):
    """
    Almacena la configuración general del salón de belleza.
    Se espera una única fila en esta tabla (patrón singleton de configuración).
    """

    __tablename__ = "configuracion_salon"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_salon: Mapped[str] = mapped_column(String(150), nullable=False, default="Mi Salón de Belleza")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ruc: Mapped[str | None] = mapped_column(String(30), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN")
    impuesto_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("18.00"))
    horario_general: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color_principal: Mapped[str] = mapped_column(String(20), nullable=False, default="#8B5CF6")
    texto_comprobante: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ConfiguracionSalon {self.nombre_salon}>"
