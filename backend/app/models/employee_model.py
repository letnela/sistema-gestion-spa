"""Modelos de las tablas `empleados`, `horarios_empleado`, `vacaciones_empleado`,
`bloqueos_horario` y la tabla de asociación `empleado_servicio`."""
import uuid
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.appointment_model import Cita
    from app.models.commission_model import Comision
    from app.models.service_model import Servicio
    from app.models.user_model import Usuario


class Empleado(Base, TimestampMixin):
    """
    Representa a un empleado del salón (usualmente un estilista).
    Puede estar vinculado opcionalmente a una cuenta de Usuario para
    permitirle iniciar sesión en el sistema.
    """

    __tablename__ = "empleados"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False, default="ESTILISTA")
    especialidad: Mapped[str | None] = mapped_column(String(150), nullable=True)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    porcentaje_comision_default: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("10.00")
    )
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    usuario: Mapped["Usuario | None"] = relationship(back_populates="empleado")
    servicios: Mapped[list["EmpleadoServicio"]] = relationship(
        back_populates="empleado", cascade="all, delete-orphan"
    )
    horarios: Mapped[list["HorarioEmpleado"]] = relationship(
        back_populates="empleado", cascade="all, delete-orphan"
    )
    vacaciones: Mapped[list["VacacionEmpleado"]] = relationship(
        back_populates="empleado", cascade="all, delete-orphan"
    )
    bloqueos: Mapped[list["BloqueoHorario"]] = relationship(
        back_populates="empleado", cascade="all, delete-orphan"
    )
    citas: Mapped[list["Cita"]] = relationship(back_populates="empleado")
    comisiones: Mapped[list["Comision"]] = relationship(back_populates="empleado")

    def __repr__(self) -> str:
        return f"<Empleado {self.nombres} {self.apellidos}>"

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo concatenado del empleado."""
        return f"{self.nombres} {self.apellidos}"


class EmpleadoServicio(Base):
    """Tabla de asociación: qué servicios puede realizar cada empleado."""

    __tablename__ = "empleado_servicio"
    __table_args__ = (UniqueConstraint("empleado_id", "servicio_id", name="uq_empleado_servicio"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="CASCADE"), nullable=False
    )
    servicio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servicios.id", ondelete="CASCADE"), nullable=False
    )

    empleado: Mapped["Empleado"] = relationship(back_populates="servicios")
    servicio: Mapped["Servicio"] = relationship(back_populates="empleados")


class HorarioEmpleado(Base):
    """
    Define el horario laboral semanal de un empleado.
    `dia_semana` usa la convención ISO: 1=Lunes ... 7=Domingo.
    """

    __tablename__ = "horarios_empleado"
    __table_args__ = (
        UniqueConstraint("empleado_id", "dia_semana", name="uq_horario_empleado_dia"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="CASCADE"), nullable=False
    )
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_entrada: Mapped[time] = mapped_column(Time, nullable=False)
    hora_salida: Mapped[time] = mapped_column(Time, nullable=False)
    hora_inicio_descanso: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_fin_descanso: Mapped[time | None] = mapped_column(Time, nullable=True)
    es_dia_libre: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    empleado: Mapped["Empleado"] = relationship(back_populates="horarios")


class VacacionEmpleado(Base):
    """Registra los periodos de vacaciones de un empleado."""

    __tablename__ = "vacaciones_empleado"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="CASCADE"), nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    empleado: Mapped["Empleado"] = relationship(back_populates="vacaciones")


class BloqueoHorario(Base):
    """
    Representa un bloqueo temporal puntual en la agenda de un empleado
    (por ejemplo, una cita médica o un permiso de unas horas).
    """

    __tablename__ = "bloqueos_horario"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empleados.id", ondelete="CASCADE"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)

    empleado: Mapped["Empleado"] = relationship(back_populates="bloqueos")
