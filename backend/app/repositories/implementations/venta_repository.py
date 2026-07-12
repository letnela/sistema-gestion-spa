"""Repositorio SQLAlchemy para ventas."""
import uuid
from datetime import date, datetime, time
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.sale_model import Venta, VentaDetalle
from app.models.product_model import Producto
from app.models.service_model import Servicio
from app.repositories.interfaces.venta_repository_interface import VentaRepositoryInterface


class VentaRepository(VentaRepositoryInterface):
    def __init__(self, db: Session): self.db = db

    def obtener_por_id(self, venta_id: uuid.UUID):
        stmt = select(Venta).options(
            joinedload(Venta.cliente), joinedload(Venta.detalles).joinedload(VentaDetalle.producto),
            joinedload(Venta.detalles).joinedload(VentaDetalle.servicio), joinedload(Venta.pagos), joinedload(Venta.comisiones)
        ).where(Venta.id == venta_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def listar(self, fecha_desde=None, fecha_hasta=None, cliente_id=None, estado=None, busqueda=None,
               pagina=1, tamano_pagina=20, orden_direccion="desc"):
        stmt = select(Venta).options(joinedload(Venta.cliente), joinedload(Venta.detalles), joinedload(Venta.pagos))
        count_stmt = select(func.count(Venta.id))
        filtros = []
        if fecha_desde: filtros.append(Venta.fecha >= datetime.combine(fecha_desde, time.min))
        if fecha_hasta: filtros.append(Venta.fecha <= datetime.combine(fecha_hasta, time.max))
        if cliente_id: filtros.append(Venta.cliente_id == cliente_id)
        if estado: filtros.append(Venta.estado == estado)
        if busqueda: filtros.append(Venta.numero_comprobante.ilike(f"%{busqueda.strip()}%"))
        if filtros:
            stmt = stmt.where(*filtros); count_stmt = count_stmt.where(*filtros)
        total = self.db.scalar(count_stmt) or 0
        order = Venta.fecha.asc() if orden_direccion == "asc" else Venta.fecha.desc()
        items = self.db.scalars(stmt.order_by(order).offset((pagina-1)*tamano_pagina).limit(tamano_pagina)).unique().all()
        return list(items), total

    def guardar(self, venta):
        self.db.add(venta); self.db.flush(); return venta
