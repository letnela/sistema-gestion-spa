"""Lógica transaccional de ventas, pagos, stock, comisiones y caja."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import (AccionAuditoria, EstadoComision, EstadoGenerico, EstadoPago, EstadoCita,
    EstadoVenta, MetodoPago, TipoComision, TipoMovimientoInventario)
from app.core.exceptions import ConflictException, InsufficientStockException, NotFoundException, ValidationException
from app.models.cash_model import CajaMovimiento, CajaSesion
from app.models.appointment_model import Cita
from app.models.client_model import Cliente
from app.models.commission_model import Comision
from app.models.employee_model import Empleado
from app.models.inventory_model import InventarioMovimiento
from app.models.payment_model import Pago
from app.models.product_model import Producto
from app.models.sale_model import Venta, VentaDetalle
from app.models.service_model import Servicio
from app.repositories.implementations.venta_repository import VentaRepository
from app.services.audit_service import registrar_auditoria

CENT = Decimal("0.01")
def money(value): return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)

class SaleService:
    def __init__(self, db: Session): self.db=db; self.repo=VentaRepository(db)

    def _numero(self):
        hoy=datetime.now().strftime("%Y%m%d")
        n=(self.db.scalar(select(func.count(Venta.id)).where(func.date(Venta.fecha)==date.today())) or 0)+1
        return f"V-{hoy}-{n:04d}"

    def obtener(self, venta_id):
        venta=self.repo.obtener_por_id(venta_id)
        if not venta: raise NotFoundException("Venta no encontrada")
        return venta

    def listar(self, **kwargs): return self.repo.listar(**kwargs)

    def crear(self, datos, actor):
        cita = None
        if datos.cita_id:
            cita = self.db.get(Cita, datos.cita_id)
            if not cita: raise NotFoundException("Cita no encontrada")
            if cita.estado != EstadoCita.FINALIZADA: raise ConflictException("Solo se pueden cobrar citas finalizadas")
            if self.db.scalar(select(Venta).where(Venta.cita_id == cita.id)): raise ConflictException("La cita ya fue cobrada")
            if datos.cliente_id and datos.cliente_id != cita.cliente_id: raise ValidationException("El cliente no corresponde a la cita")
            datos.cliente_id = cita.cliente_id
        if datos.cliente_id and not self.db.get(Cliente, datos.cliente_id): raise NotFoundException("Cliente no encontrado")
        detalles=[]; subtotal=Decimal("0.00")
        stock_changes=[]; comisiones=[]
        for item in datos.detalles:
            if item.producto_id:
                producto=self.db.scalar(select(Producto).where(Producto.id==item.producto_id).with_for_update())
                if not producto or producto.estado!=EstadoGenerico.ACTIVO: raise NotFoundException("Producto no encontrado o inactivo")
                if producto.stock < item.cantidad: raise InsufficientStockException(f"Stock insuficiente para {producto.nombre}")
                precio=money(producto.precio_venta); descripcion=producto.nombre
                producto.stock -= item.cantidad
                stock_changes.append((producto,item.cantidad))
            else:
                servicio=self.db.get(Servicio,item.servicio_id)
                empleado=self.db.get(Empleado,item.empleado_id)
                if not servicio or servicio.estado!=EstadoGenerico.ACTIVO: raise NotFoundException("Servicio no encontrado o inactivo")
                if not empleado or empleado.estado!=EstadoGenerico.ACTIVO: raise NotFoundException("Empleado no encontrado o inactivo")
                precio=money(servicio.precio); descripcion=servicio.nombre
            bruto=money(precio*item.cantidad)
            if item.descuento > bruto: raise ValidationException(f"El descuento de {descripcion} supera su importe")
            linea=money(bruto-item.descuento); subtotal += linea
            detalles.append((item,precio,linea,descripcion))
            if item.servicio_id:
                porcentaje=money(getattr(servicio,"porcentaje_comision",None) or empleado.porcentaje_comision_default)
                comisiones.append((empleado,linea,porcentaje))
        subtotal=money(subtotal)
        if datos.descuento_global > subtotal: raise ValidationException("El descuento global supera el subtotal")
        base=money(subtotal-datos.descuento_global)
        impuesto=money(base*Decimal(datos.porcentaje_impuesto)/Decimal("100")); total=money(base+impuesto)
        pagado=money(sum((p.monto for p in datos.pagos),Decimal("0.00")))
        if pagado != total: raise ValidationException(f"Los pagos ({pagado}) deben cubrir exactamente el total ({total})")

        venta=Venta(numero_comprobante=self._numero(),cliente_id=datos.cliente_id,cita_id=datos.cita_id,usuario_id=actor.id,
            subtotal=subtotal,descuento=money(datos.descuento_global),impuesto=impuesto,total=total,
            estado=EstadoVenta.COMPLETADA,created_by=actor.id,updated_by=actor.id)
        self.repo.guardar(venta)
        for item,precio,linea,_ in detalles:
            venta.detalles.append(VentaDetalle(producto_id=item.producto_id,servicio_id=item.servicio_id,
                empleado_id=item.empleado_id,cantidad=item.cantidad,precio_unitario=precio,
                descuento=money(item.descuento),subtotal=linea))
        for p in datos.pagos:
            venta.pagos.append(Pago(usuario_id=actor.id,monto=money(p.monto),metodo=p.metodo,
                referencia=p.referencia,estado=EstadoPago.COMPLETO))
        self.db.flush()
        for producto,cantidad in stock_changes:
            self.db.add(InventarioMovimiento(producto_id=producto.id,tipo=TipoMovimientoInventario.SALIDA,
                cantidad=cantidad,stock_resultante=producto.stock,motivo=f"Venta {venta.numero_comprobante}",usuario_id=actor.id))
        for empleado,base_comision,porcentaje in comisiones:
            self.db.add(Comision(empleado_id=empleado.id,venta_id=venta.id,tipo=TipoComision.SERVICIO,
                monto_base=base_comision,porcentaje_aplicado=porcentaje,
                monto_comision=money(base_comision*porcentaje/Decimal("100")),estado=EstadoComision.PENDIENTE,
                periodo=date.today()))
        caja=self.db.scalar(select(CajaSesion).where(CajaSesion.estado=="ABIERTA").order_by(CajaSesion.fecha_apertura.desc()))
        efectivo=money(sum((p.monto for p in datos.pagos if p.metodo==MetodoPago.EFECTIVO),Decimal("0.00")))
        if efectivo>0 and caja:
            self.db.add(CajaMovimiento(caja_sesion_id=caja.id,usuario_id=actor.id,tipo="INGRESO",
                concepto=f"Venta {venta.numero_comprobante}",monto=efectivo,referencia=str(venta.id)))
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,"VENTAS","Venta",str(venta.id),valor_nuevo={"numero":venta.numero_comprobante,"total":str(total)})
        self.db.commit(); return self.obtener(venta.id)

    def anular(self, venta_id, motivo, actor):
        venta=self.obtener(venta_id)
        if venta.estado==EstadoVenta.ANULADA: raise ConflictException("La venta ya está anulada")
        for d in venta.detalles:
            if d.producto_id:
                producto=self.db.scalar(select(Producto).where(Producto.id==d.producto_id).with_for_update())
                producto.stock += d.cantidad
                self.db.add(InventarioMovimiento(producto_id=producto.id,tipo=TipoMovimientoInventario.ENTRADA,
                    cantidad=d.cantidad,stock_resultante=producto.stock,motivo=f"Anulación {venta.numero_comprobante}",usuario_id=actor.id))
        for p in venta.pagos: p.estado=EstadoPago.ANULADO
        for c in venta.comisiones:
            if c.estado==EstadoComision.PAGADA: raise ConflictException("No se puede anular una venta con comisiones pagadas")
            self.db.delete(c)
        venta.estado=EstadoVenta.ANULADA; venta.motivo_anulacion=motivo; venta.updated_by=actor.id
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CANCELAR,"VENTAS","Venta",str(venta.id),valor_nuevo={"motivo":motivo})
        self.db.commit(); return self.obtener(venta.id)

