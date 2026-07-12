import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

class PedidoOnline(Base, TimestampMixin):
    __tablename__ = 'pedidos_online'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default='PENDIENTE')
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    descuento: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False, default=Decimal('0'))
    total: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    modalidad_entrega: Mapped[str] = mapped_column(String(30), nullable=False, default='RECOJO_SALON')
    direccion_entrega: Mapped[str|None] = mapped_column(String(300), nullable=True)
    metodo_pago: Mapped[str] = mapped_column(String(30), nullable=False, default='PAGO_EN_SALON')
    notas: Mapped[str|None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cliente = relationship('Cliente')
    detalles: Mapped[list['PedidoOnlineDetalle']] = relationship(back_populates='pedido', cascade='all, delete-orphan')

class PedidoOnlineDetalle(Base):
    __tablename__ = 'pedido_online_detalles'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('pedidos_online.id', ondelete='CASCADE'), nullable=False)
    producto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('productos.id', ondelete='RESTRICT'), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    pedido = relationship('PedidoOnline', back_populates='detalles')
    producto = relationship('Producto')
