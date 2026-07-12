"""Modelo de la tabla `inventario_movimientos` (Kardex)."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import TipoMovimientoInventario
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.product_model import Producto
    from app.models.user_model import Usuario


class InventarioMovimiento(Base):
    """
    Registra cada movimiento de inventario (entrada, salida o ajuste),
    conformando el kardex histórico de cada producto.
    """

    __tablename__ = "inventario_movimientos"
    __table_args__ = (
        CheckConstraint(
            f"tipo IN {tuple(TipoMovimientoInventario.TODOS)}", name="ck_inventario_tipo_valido"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    producto: Mapped["Producto"] = relationship(back_populates="movimientos")
    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<InventarioMovimiento {self.tipo} producto={self.producto_id} cantidad={self.cantidad}>"
