"""Modelos de las tablas `categorias_producto` y `productos`."""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoGenerico
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory_model import InventarioMovimiento
    from app.models.promotion_model import PromocionProducto
    from app.models.sale_model import VentaDetalle
    from app.models.supplier_model import Proveedor, ProveedorProducto


class CategoriaProducto(Base, TimestampMixin):
    """Agrupa los productos en categorías (ej. Shampoo, Coloración, Herramientas)."""

    __tablename__ = "categorias_producto"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    productos: Mapped[list["Producto"]] = relationship(back_populates="categoria")

    def __repr__(self) -> str:
        return f"<CategoriaProducto {self.nombre}>"


class Producto(Base, TimestampMixin):
    """Representa un producto físico vendido o utilizado en el salón."""

    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categorias_producto.id", ondelete="RESTRICT"), nullable=False
    )
    proveedor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("proveedores.id", ondelete="SET NULL"), nullable=True
    )
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_compra: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    codigo_barras: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    unidad_medida: Mapped[str] = mapped_column(String(30), nullable=False, default="UNIDAD")
    stock_maximo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_vencimiento: Mapped[object | None] = mapped_column(Date, nullable=True)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=EstadoGenerico.ACTIVO)

    categoria: Mapped["CategoriaProducto"] = relationship(back_populates="productos")
    proveedor: Mapped["Proveedor | None"] = relationship(back_populates="productos")
    movimientos: Mapped[list["InventarioMovimiento"]] = relationship(back_populates="producto")
    detalles_venta: Mapped[list["VentaDetalle"]] = relationship(back_populates="producto")
    promociones: Mapped[list["PromocionProducto"]] = relationship(back_populates="producto")
    proveedores: Mapped[list["ProveedorProducto"]] = relationship(back_populates="producto")

    def __repr__(self) -> str:
        return f"<Producto {self.codigo} - {self.nombre}>"

    @property
    def tiene_stock_bajo(self) -> bool:
        """Indica si el stock actual está en o por debajo del stock mínimo."""
        return self.stock <= self.stock_minimo
