"""Modelos de las tablas `usuarios` e `intentos_login`."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role_model import Rol
    from app.models.employee_model import Empleado
    from app.models.client_model import Cliente


class Usuario(Base, TimestampMixin):
    """
    Representa una cuenta de acceso al sistema.
    Un usuario puede estar o no vinculado a un registro de empleado
    (los administradores y recepcionistas normalmente no lo están).
    """

    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_password_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_password_expira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")
    empleado: Mapped["Empleado | None"] = relationship(back_populates="usuario", uselist=False)
    cliente: Mapped["Cliente | None"] = relationship(foreign_keys=[cliente_id], uselist=False)
    intentos_login: Mapped[list["IntentoLogin"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.correo}>"


class IntentoLogin(Base):
    """
    Registra cada intento de inicio de sesión (exitoso o fallido) para
    fines de auditoría y para implementar el bloqueo temporal de cuentas.
    """

    __tablename__ = "intentos_login"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True
    )
    correo_intentado: Mapped[str] = mapped_column(String(150), nullable=False)
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_origen: Mapped[str | None] = mapped_column(String(50), nullable=True)
    navegador: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    usuario: Mapped["Usuario | None"] = relationship(back_populates="intentos_login")

    def __repr__(self) -> str:
        return f"<IntentoLogin {self.correo_intentado} exitoso={self.exitoso}>"
