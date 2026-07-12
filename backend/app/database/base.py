"""
Base declarativa de SQLAlchemy y mixins reutilizables por todos los modelos.
Incluye columnas de auditoría estándar (created_at, updated_at, created_by, updated_by).
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM del sistema."""
    pass


class TimestampMixin:
    """
    Mixin que agrega columnas de fecha de creación y actualización
    a cualquier modelo que lo herede.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AuditUserMixin:
    """
    Mixin que agrega referencias al usuario que creó y actualizó el registro.
    Las columnas son nullables porque el primer seed no tiene un usuario previo.
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
