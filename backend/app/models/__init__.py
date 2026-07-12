"""
Punto central de importación de todos los modelos ORM.
Alembic y SQLAlchemy usan este módulo para detectar todas las tablas
al generar migraciones automáticas (`Base.metadata`).
"""
from app.database.base import Base

# Importar todos los modelos para que se registren en Base.metadata
from app.models.role_model import Rol  # noqa: E402,F401
from app.models.user_model import Usuario, IntentoLogin  # noqa: E402,F401
from app.models.client_model import Cliente  # noqa: E402,F401
from app.models.employee_model import (  # noqa: E402,F401
    Empleado,
    EmpleadoServicio,
    HorarioEmpleado,
    VacacionEmpleado,
    BloqueoHorario,
)
from app.models.service_model import CategoriaServicio, Servicio  # noqa: E402,F401
from app.models.appointment_model import Cita, CitaServicio  # noqa: E402,F401
from app.models.product_model import CategoriaProducto, Producto  # noqa: E402,F401
from app.models.inventory_model import InventarioMovimiento  # noqa: E402,F401
from app.models.purchase_model import Compra, CompraDetalle  # noqa: E402,F401
from app.models.supplier_model import Proveedor, ProveedorProducto  # noqa: E402,F401
from app.models.sale_model import Venta, VentaDetalle  # noqa: E402,F401
from app.models.payment_model import Pago  # noqa: E402,F401
from app.models.cash_model import CajaSesion, CajaMovimiento  # noqa: E402,F401
from app.models.promotion_model import Promocion, PromocionServicio, PromocionProducto  # noqa: E402,F401
from app.models.commission_model import Comision  # noqa: E402,F401
from app.models.audit_model import Auditoria, Notificacion  # noqa: E402,F401
from app.models.salon_config_model import ConfiguracionSalon  # noqa: E402,F401
from app.models.online_order_model import PedidoOnline, PedidoOnlineDetalle  # noqa: E402,F401
from app.models.chat_model import ChatMensaje  # noqa: E402,F401

__all__ = [
    "Base",
    "Rol",
    "Usuario",
    "IntentoLogin",
    "Cliente",
    "Empleado",
    "EmpleadoServicio",
    "HorarioEmpleado",
    "VacacionEmpleado",
    "BloqueoHorario",
    "CategoriaServicio",
    "Servicio",
    "Cita",
    "CitaServicio",
    "CategoriaProducto",
    "Producto",
    "InventarioMovimiento",
    "Compra",
    "CompraDetalle",
    "Proveedor",
    "ProveedorProducto",
    "Venta",
    "VentaDetalle",
    "Pago",
    "CajaSesion",
    "CajaMovimiento",
    "Promocion",
    "PromocionServicio",
    "PromocionProducto",
    "Comision",
    "Auditoria",
    "Notificacion",
    "ConfiguracionSalon",
    "PedidoOnline",
    "PedidoOnlineDetalle",
    "ChatMensaje",
]
