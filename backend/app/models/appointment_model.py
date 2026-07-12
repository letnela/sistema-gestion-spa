"""Modelos de las tablas `citas` y `cita_servicios`."""
import uuid
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoCita
from app.database.base import AuditUserMixin, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.client_model import Cliente
    from app.models.employee_model import Empleado
    from app.models.service_model import Servicio


class Cita(Base, TimestampMixin, AuditUserMixin):
    """
    Representa una cita agendada de un cliente con un empleado.
    Una cita puede incluir uno o varios servicios (ver `CitaServicio`).
    """

    __tablename__ = "citas"
    __table_args__ = (
        CheckConstraint(
            f"estado IN {tuple(EstadoCita.TODOS)}", name="ck_citas_estado_valido"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    duracion_total_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    precio_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoCita.PENDIENTE)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="citas")
    empleado: Mapped["Empleado"] = relationship(back_populates="citas")
    servicios: Mapped[list["CitaServicio"]] = relationship(
        back_populates="cita", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cita {self.id} estado={self.estado}>"


class CitaServicio(Base):
    """Detalle de los servicios incluidos en una cita, con su precio congelado."""

    __tablename__ = "cita_servicios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cita_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("citas.id", ondelete="CASCADE"), nullable=False)
    servicio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=False
    )
    precio_aplicado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duracion_aplicada_minutos: Mapped[int] = mapped_column(Integer, nullable=False)

    cita: Mapped["Cita"] = relationship(back_populates="servicios")
    servicio: Mapped["Servicio"] = relationship(back_populates="citas")
