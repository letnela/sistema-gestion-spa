"""Modelos de las tablas `proveedores` y `proveedor_producto`."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product_model import Producto
    from app.models.purchase_model import Compra


class Proveedor(Base, TimestampMixin):
    """Representa a un proveedor de productos del salón."""

    __tablename__ = "proveedores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    razon_social: Mapped[str] = mapped_column(String(150), nullable=False)
    documento_ruc: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contacto_nombre: Mapped[str | None] = mapped_column(String(150), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    productos: Mapped[list["Producto"]] = relationship(back_populates="proveedor")
    compras: Mapped[list["Compra"]] = relationship(back_populates="proveedor")
    productos_suministrados: Mapped[list["ProveedorProducto"]] = relationship(
        back_populates="proveedor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Proveedor {self.razon_social}>"


class ProveedorProducto(Base):
    """
    Tabla de asociación entre proveedores y productos que suministran,
    permitiendo registrar un precio de compra específico por proveedor.
    """

    __tablename__ = "proveedor_producto"
    __table_args__ = (
        UniqueConstraint("proveedor_id", "producto_id", name="uq_proveedor_producto"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proveedor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False
    )
    producto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )

    proveedor: Mapped["Proveedor"] = relationship(back_populates="productos_suministrados")
    producto: Mapped["Producto"] = relationship(back_populates="proveedores")
