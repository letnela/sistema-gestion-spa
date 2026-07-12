"""Consultas agregadas para Dashboard y Reportes de la Fase 9."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session

from app.core.constants import EstadoCita, EstadoVenta
from app.models.appointment_model import Cita, CitaServicio
from app.models.client_model import Cliente
from app.models.employee_model import Empleado
from app.models.payment_model import Pago
from app.models.product_model import Producto
from app.models.sale_model import Venta, VentaDetalle
from app.models.service_model import Servicio
from app.schemas.report_schema import (
    DashboardResponse, EstadoCitaItem, IndicadoresDashboard, RankingItem,
    ReporteCitasResponse, ReporteInventarioResponse, ReporteVentasResponse,
    SerieTemporalItem,
)

D0 = Decimal("0.00")


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _dt(desde: date, hasta: date):
        return datetime.combine(desde, time.min), datetime.combine(hasta + timedelta(days=1), time.min)

    @staticmethod
    def _decimal(value) -> Decimal:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    def _ventas_query(self, desde: date, hasta: date):
        ini, fin = self._dt(desde, hasta)
        return self.db.query(Venta).filter(Venta.fecha >= ini, Venta.fecha < fin, Venta.estado == EstadoVenta.COMPLETADA)

    def ventas_por_dia(self, desde: date, hasta: date):
        ini, fin = self._dt(desde, hasta)
        rows = self.db.query(
            cast(Venta.fecha, Date).label("dia"), func.coalesce(func.sum(Venta.total), 0), func.count(Venta.id)
        ).filter(Venta.fecha >= ini, Venta.fecha < fin, Venta.estado == EstadoVenta.COMPLETADA).group_by("dia").order_by("dia").all()
        mapa = {r[0]: (r[1], r[2]) for r in rows}
        salida=[]; actual=desde
        while actual <= hasta:
            total,cantidad=mapa.get(actual,(0,0)); salida.append(SerieTemporalItem(fecha=actual,total=self._decimal(total),cantidad=int(cantidad)))
            actual += timedelta(days=1)
        return salida

    def citas_estados(self, desde: date, hasta: date):
        rows=self.db.query(Cita.estado,func.count(Cita.id)).filter(Cita.fecha.between(desde,hasta)).group_by(Cita.estado).all()
        total=sum(int(x[1]) for x in rows)
        return [EstadoCitaItem(estado=x[0],cantidad=int(x[1]),porcentaje=self._decimal((int(x[1])*100/total) if total else 0)) for x in rows]

    def top_servicios(self, desde: date, hasta: date, limite=5):
        rows=self.db.query(Servicio.id,Servicio.nombre,func.count(CitaServicio.id),func.coalesce(func.sum(CitaServicio.precio_aplicado),0)).join(CitaServicio,CitaServicio.servicio_id==Servicio.id).join(Cita,Cita.id==CitaServicio.cita_id).filter(Cita.fecha.between(desde,hasta),Cita.estado==EstadoCita.FINALIZADA).group_by(Servicio.id,Servicio.nombre).order_by(func.count(CitaServicio.id).desc()).limit(limite).all()
        return [RankingItem(id=str(r[0]),nombre=r[1],cantidad=int(r[2]),total=self._decimal(r[3])) for r in rows]

    def top_productos(self, desde: date, hasta: date, limite=5):
        ini,fin=self._dt(desde,hasta)
        rows=self.db.query(Producto.id,Producto.nombre,func.coalesce(func.sum(VentaDetalle.cantidad),0),func.coalesce(func.sum(VentaDetalle.subtotal),0)).join(VentaDetalle,VentaDetalle.producto_id==Producto.id).join(Venta,Venta.id==VentaDetalle.venta_id).filter(Venta.fecha>=ini,Venta.fecha<fin,Venta.estado==EstadoVenta.COMPLETADA).group_by(Producto.id,Producto.nombre).order_by(func.sum(VentaDetalle.cantidad).desc()).limit(limite).all()
        return [RankingItem(id=str(r[0]),nombre=r[1],cantidad=int(r[2]),total=self._decimal(r[3])) for r in rows]

    def top_empleados(self, desde: date, hasta: date, limite=5):
        rows=self.db.query(Empleado.id,Empleado.nombres,Empleado.apellidos,func.count(Cita.id),func.coalesce(func.sum(Cita.precio_total),0)).join(Cita,Cita.empleado_id==Empleado.id).filter(Cita.fecha.between(desde,hasta),Cita.estado==EstadoCita.FINALIZADA).group_by(Empleado.id,Empleado.nombres,Empleado.apellidos).order_by(func.sum(Cita.precio_total).desc()).limit(limite).all()
        return [RankingItem(id=str(r[0]),nombre=f"{r[1]} {r[2]}",cantidad=int(r[3]),total=self._decimal(r[4])) for r in rows]

    def dashboard(self, desde: date, hasta: date):
        q=self._ventas_query(desde,hasta)
        agg=q.with_entities(func.coalesce(func.sum(Venta.total),0),func.count(Venta.id)).one()
        hoy=date.today(); ini_hoy,fin_hoy=self._dt(hoy,hoy)
        ventas_hoy=self.db.query(func.coalesce(func.sum(Venta.total),0)).filter(Venta.fecha>=ini_hoy,Venta.fecha<fin_hoy,Venta.estado==EstadoVenta.COMPLETADA).scalar()
        citas_total=self.db.query(func.count(Cita.id)).filter(Cita.fecha.between(desde,hasta)).scalar() or 0
        finalizadas=self.db.query(func.count(Cita.id)).filter(Cita.fecha.between(desde,hasta),Cita.estado==EstadoCita.FINALIZADA).scalar() or 0
        canceladas=self.db.query(func.count(Cita.id)).filter(Cita.fecha.between(desde,hasta),Cita.estado==EstadoCita.CANCELADA).scalar() or 0
        citas_hoy=self.db.query(func.count(Cita.id)).filter(Cita.fecha==hoy).scalar() or 0
        clientes_nuevos=self.db.query(func.count(Cliente.id)).filter(cast(Cliente.created_at,Date).between(desde,hasta),Cliente.eliminado.is_(False)).scalar() or 0
        bajos=self.db.query(func.count(Producto.id)).filter(Producto.stock<=Producto.stock_minimo).scalar() or 0
        valor=self.db.query(func.coalesce(func.sum(Producto.stock*Producto.precio_compra),0)).scalar()
        total=self._decimal(agg[0]); cantidad=int(agg[1])
        indicadores=IndicadoresDashboard(ventas_hoy=self._decimal(ventas_hoy),ventas_periodo=total,cantidad_ventas=cantidad,ticket_promedio=self._decimal(total/cantidad if cantidad else 0),citas_hoy=int(citas_hoy),citas_periodo=int(citas_total),citas_finalizadas=int(finalizadas),citas_canceladas=int(canceladas),clientes_nuevos=int(clientes_nuevos),productos_stock_bajo=int(bajos),valor_inventario=self._decimal(valor))
        return DashboardResponse(fecha_desde=desde,fecha_hasta=hasta,indicadores=indicadores,ventas_por_dia=self.ventas_por_dia(desde,hasta),citas_por_estado=self.citas_estados(desde,hasta),servicios_mas_vendidos=self.top_servicios(desde,hasta),productos_mas_vendidos=self.top_productos(desde,hasta),empleados_destacados=self.top_empleados(desde,hasta))

    def reporte_ventas(self, desde: date, hasta: date):
        q=self._ventas_query(desde,hasta)
        r=q.with_entities(func.coalesce(func.sum(Venta.subtotal),0),func.coalesce(func.sum(Venta.descuento),0),func.coalesce(func.sum(Venta.impuesto),0),func.coalesce(func.sum(Venta.total),0),func.count(Venta.id)).one()
        ini,fin=self._dt(desde,hasta)
        pagos=self.db.query(Pago.metodo,func.count(Pago.id),func.coalesce(func.sum(Pago.monto),0)).join(Venta,Venta.id==Pago.venta_id).filter(Venta.fecha>=ini,Venta.fecha<fin,Venta.estado==EstadoVenta.COMPLETADA).group_by(Pago.metodo).all()
        cantidad=int(r[4]); total=self._decimal(r[3])
        return ReporteVentasResponse(fecha_desde=desde,fecha_hasta=hasta,total_bruto=self._decimal(r[0]),descuentos=self._decimal(r[1]),impuestos=self._decimal(r[2]),total_neto=total,cantidad_ventas=cantidad,ticket_promedio=self._decimal(total/cantidad if cantidad else 0),ventas_por_dia=self.ventas_por_dia(desde,hasta),metodos_pago=[RankingItem(nombre=x[0],cantidad=int(x[1]),total=self._decimal(x[2])) for x in pagos])

    def reporte_citas(self, desde: date, hasta: date):
        estados=self.citas_estados(desde,hasta); mapa={x.estado:x.cantidad for x in estados}; total=sum(mapa.values()); fin=mapa.get(EstadoCita.FINALIZADA,0)
        return ReporteCitasResponse(fecha_desde=desde,fecha_hasta=hasta,total=total,finalizadas=fin,canceladas=mapa.get(EstadoCita.CANCELADA,0),no_asistio=mapa.get(EstadoCita.NO_ASISTIO,0),tasa_finalizacion=self._decimal(fin*100/total if total else 0),estados=estados,servicios=self.top_servicios(desde,hasta,10),empleados=self.top_empleados(desde,hasta,10))

    def reporte_inventario(self):
        rows=self.db.query(func.count(Producto.id),func.coalesce(func.sum(Producto.stock),0),func.coalesce(func.sum(Producto.stock*Producto.precio_compra),0),func.coalesce(func.sum(Producto.stock*Producto.precio_venta),0)).one()
        agotados=self.db.query(func.count(Producto.id)).filter(Producto.stock<=0).scalar() or 0
        bajos=self.db.query(func.count(Producto.id)).filter(Producto.stock<=Producto.stock_minimo).scalar() or 0
        crit=self.db.query(Producto.id,Producto.nombre,Producto.stock,Producto.stock*Producto.precio_compra).filter(Producto.stock<=Producto.stock_minimo).order_by(Producto.stock.asc()).limit(20).all()
        return ReporteInventarioResponse(cantidad_productos=int(rows[0]),agotados=int(agotados),stock_bajo=int(bajos),unidades_totales=int(rows[1]),valor_costo=self._decimal(rows[2]),valor_venta=self._decimal(rows[3]),productos_criticos=[RankingItem(id=str(x[0]),nombre=x[1],cantidad=int(x[2]),total=self._decimal(x[3])) for x in crit])

    def exportar_ventas_xlsx(self, desde: date, hasta: date) -> bytes:
        rep=self.reporte_ventas(desde,hasta); wb=Workbook(); ws=wb.active; ws.title="Ventas"
        ws.append(["Fecha","Cantidad de ventas","Total"])
        for x in rep.ventas_por_dia: ws.append([x.fecha.isoformat(),x.cantidad,float(x.total)])
        ws.append([]); ws.append(["Total neto",float(rep.total_neto)]); ws.append(["Ticket promedio",float(rep.ticket_promedio)])
        out=BytesIO(); wb.save(out); return out.getvalue()

    def exportar_resumen_pdf(self, desde: date, hasta: date) -> bytes:
        d=self.dashboard(desde,hasta); out=BytesIO(); c=canvas.Canvas(out,pagesize=A4); y=800
        c.setFont("Helvetica-Bold",16); c.drawString(40,y,"Reporte ejecutivo del salón"); y-=30
        c.setFont("Helvetica",10); c.drawString(40,y,f"Periodo: {desde.isoformat()} al {hasta.isoformat()}"); y-=30
        for label,value in [("Ventas",d.indicadores.ventas_periodo),("Cantidad de ventas",d.indicadores.cantidad_ventas),("Citas",d.indicadores.citas_periodo),("Citas finalizadas",d.indicadores.citas_finalizadas),("Clientes nuevos",d.indicadores.clientes_nuevos),("Stock bajo",d.indicadores.productos_stock_bajo)]:
            c.drawString(40,y,f"{label}: {value}"); y-=20
        c.save(); return out.getvalue()
