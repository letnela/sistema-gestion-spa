"""Modelo de la tabla `clientes`."""
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import AuditUserMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.appointment_model import Cita
    from app.models.sale_model import Venta


class Cliente(Base, TimestampMixin, AuditUserMixin):
    """
    Representa a un cliente del salón de belleza.
    Incluye datos de contacto, preferencias y alergias relevantes
    para la prestación segura de los servicios.
    """

    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferencias: Mapped[str | None] = mapped_column(Text, nullable=True)
    alergias: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    citas: Mapped[list["Cita"]] = relationship(back_populates="cliente")
    ventas: Mapped[list["Venta"]] = relationship(back_populates="cliente")

    def __repr__(self) -> str:
        return f"<Cliente {self.nombres} {self.apellidos}>"

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo concatenado del cliente."""
        return f"{self.nombres} {self.apellidos}"
