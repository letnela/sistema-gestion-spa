"""Fase 15: finanzas, comisiones, cobros pendientes, auditoría y notificaciones."""
import io, uuid
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_current_user, get_db
from app.core.constants import RolesSistema, EstadoComision, EstadoCita, EstadoVenta, AccionAuditoria
from app.core.permissions import require_roles
from app.core.exceptions import NotFoundException, ConflictException, UnauthorizedException
from app.models.user_model import Usuario
from app.models.employee_model import Empleado
from app.models.client_model import Cliente
from app.models.commission_model import Comision
from app.models.cash_model import CajaSesion
from app.models.sale_model import Venta
from app.models.appointment_model import Cita
from app.models.audit_model import Auditoria, Notificacion
from app.services.audit_service import registrar_auditoria

router=APIRouter(tags=["Fase 15 - Finanzas y operaciones"])

def _commission(c):
    return {"id":str(c.id),"empleado_id":str(c.empleado_id),"empleado_nombre":c.empleado.nombre_completo,
      "venta_id":str(c.venta_id) if c.venta_id else None,"tipo":c.tipo,"monto_base":c.monto_base,
      "porcentaje_aplicado":c.porcentaje_aplicado,"monto_comision":c.monto_comision,
      "estado":c.estado,"periodo":c.periodo,"fecha_pago":c.fecha_pago,"fecha":c.fecha}

@router.get('/finance/commissions/my')
def mis_comisiones(fecha_desde:date|None=Query(None),fecha_hasta:date|None=Query(None),
 user:Usuario=Depends(require_roles(RolesSistema.ESTILISTA)),db:Session=Depends(get_db)):
    empleado=db.scalar(select(Empleado).where(Empleado.usuario_id==user.id))
    if not empleado: raise NotFoundException('La cuenta no está vinculada a un empleado')
    q=select(Comision).options(joinedload(Comision.empleado)).where(Comision.empleado_id==empleado.id)
    if fecha_desde:q=q.where(Comision.periodo>=fecha_desde)
    if fecha_hasta:q=q.where(Comision.periodo<=fecha_hasta)
    items=list(db.scalars(q.order_by(Comision.periodo.desc())))
    pendiente=sum((x.monto_comision for x in items if x.estado==EstadoComision.PENDIENTE),Decimal('0'))
    pagada=sum((x.monto_comision for x in items if x.estado==EstadoComision.PAGADA),Decimal('0'))
    return {"data":{"items":[_commission(x) for x in items],"total":len(items),"pendiente":pendiente,"pagada":pagada}}

@router.get('/finance/commissions')
def comisiones(empleado_id:uuid.UUID|None=Query(None),estado:str|None=Query(None),
 user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR)),db:Session=Depends(get_db)):
    q=select(Comision).options(joinedload(Comision.empleado))
    if empleado_id:q=q.where(Comision.empleado_id==empleado_id)
    if estado:q=q.where(Comision.estado==estado)
    items=list(db.scalars(q.order_by(Comision.periodo.desc())))
    pendiente=sum((x.monto_comision for x in items if x.estado==EstadoComision.PENDIENTE),Decimal('0'))
    pagada=sum((x.monto_comision for x in items if x.estado==EstadoComision.PAGADA),Decimal('0'))
    return {"data":{"items":[_commission(x) for x in items],"total":len(items),
      "pendiente":pendiente,"pagada":pagada,"monto_total":pendiente+pagada}}

@router.patch('/finance/commissions/{comision_id}/pay')
def pagar_comision(comision_id:uuid.UUID,user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR)),db:Session=Depends(get_db)):
    from datetime import datetime, timezone
    c=db.get(Comision,comision_id)
    if not c: raise NotFoundException('Comisión no encontrada')
    if c.estado==EstadoComision.PAGADA: raise ConflictException('La comisión ya fue pagada')
    c.estado=EstadoComision.PAGADA;c.fecha_pago=datetime.now(timezone.utc)
    registrar_auditoria(db,user.id,AccionAuditoria.PAGAR,'COMISIONES','Comision',str(c.id),valor_nuevo={"estado":"PAGADA"})
    db.commit();return {"message":"Comisión pagada","data":_commission(c)}

@router.get('/finance/pending-charges')
def cobros_pendientes(user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA)),db:Session=Depends(get_db)):
    sold=select(Venta.cita_id).where(Venta.cita_id.is_not(None),Venta.estado==EstadoVenta.COMPLETADA)
    citas=list(db.scalars(select(Cita).options(joinedload(Cita.cliente),joinedload(Cita.empleado),joinedload(Cita.servicios)).where(
      Cita.estado==EstadoCita.FINALIZADA,Cita.id.not_in(sold)).order_by(Cita.fecha.desc(),Cita.hora_inicio.desc())))
    return {"data":[{"id":str(x.id),"cliente_id":str(x.cliente_id),"cliente_nombre":x.cliente.nombre_completo,
      "empleado_id":str(x.empleado_id),"empleado_nombre":x.empleado.nombre_completo,"fecha":x.fecha,
      "hora_inicio":x.hora_inicio,"precio_total":x.precio_total,"servicios":[{"id":str(y.servicio_id),"nombre":y.servicio.nombre,"precio":y.precio_aplicado} for y in x.servicios]} for x in citas]}

@router.get('/finance/cash/history')
def historial_caja(pagina:int=Query(1,ge=1),tamano:int=Query(20,ge=1,le=100),
 user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA)),db:Session=Depends(get_db)):
    q=select(CajaSesion).options(joinedload(CajaSesion.movimientos)).order_by(CajaSesion.fecha_apertura.desc())
    total=db.scalar(select(func.count(CajaSesion.id))) or 0
    items=list(db.scalars(q.offset((pagina-1)*tamano).limit(tamano)).unique())
    return {"data":{"items":[{"id":str(x.id),"fecha_apertura":x.fecha_apertura,"fecha_cierre":x.fecha_cierre,
      "monto_apertura":x.monto_apertura,"monto_cierre_calculado":x.monto_cierre_calculado,
      "monto_cierre_declarado":x.monto_cierre_declarado,"diferencia":x.diferencia,"estado":x.estado,
      "movimientos":len(x.movimientos)} for x in items],"total":total,"pagina":pagina}}

@router.post('/finance/cash/{sesion_id}/reopen')
def reabrir_caja(sesion_id:uuid.UUID,user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR)),db:Session=Depends(get_db)):
    if db.scalar(select(CajaSesion).where(CajaSesion.estado=='ABIERTA')): raise ConflictException('Ya existe una caja abierta')
    caja=db.get(CajaSesion,sesion_id)
    if not caja: raise NotFoundException('Sesión de caja no encontrada')
    anterior={"estado":caja.estado,"fecha_cierre":str(caja.fecha_cierre)}
    caja.estado='ABIERTA';caja.fecha_cierre=None;caja.usuario_cierre_id=None;caja.monto_cierre_declarado=None;caja.monto_cierre_calculado=None;caja.diferencia=None
    registrar_auditoria(db,user.id,AccionAuditoria.EDITAR,'CAJA','CajaSesion',str(caja.id),valor_anterior=anterior,valor_nuevo={"estado":"ABIERTA"})
    db.commit();return {"message":"Caja reabierta correctamente"}

@router.get('/finance/audit')
def auditoria(modulo:str|None=Query(None),accion:str|None=Query(None),pagina:int=Query(1,ge=1),tamano:int=Query(30,ge=1,le=100),
 user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR)),db:Session=Depends(get_db)):
    q=select(Auditoria).order_by(Auditoria.fecha.desc())
    if modulo:q=q.where(Auditoria.modulo==modulo)
    if accion:q=q.where(Auditoria.accion==accion)
    items=list(db.scalars(q.offset((pagina-1)*tamano).limit(tamano)))
    return {"data":[{"id":str(x.id),"usuario_id":str(x.usuario_id) if x.usuario_id else None,"accion":x.accion,
      "modulo":x.modulo,"entidad":x.entidad,"entidad_id":x.entidad_id,"valor_anterior":x.valor_anterior,
      "valor_nuevo":x.valor_nuevo,"ip_origen":x.ip_origen,"fecha":x.fecha} for x in items]}

@router.get('/client-portal/purchases')
def compras_cliente(user:Usuario=Depends(require_roles(RolesSistema.CLIENTE)),db:Session=Depends(get_db)):
    if not user.cliente_id: raise UnauthorizedException('Cuenta no vinculada a cliente')
    items=list(db.scalars(select(Venta).options(joinedload(Venta.detalles),joinedload(Venta.pagos)).where(
      Venta.cliente_id==user.cliente_id).order_by(Venta.fecha.desc())).unique())
    return {"data":[{"id":str(x.id),"numero_comprobante":x.numero_comprobante,"fecha":x.fecha,"total":x.total,
      "estado":x.estado,"pagos":[{"metodo":p.metodo,"monto":p.monto} for p in x.pagos],"cantidad_items":len(x.detalles)} for x in items]}

@router.get('/client-portal/purchases/{venta_id}/receipt.pdf')
def comprobante_cliente(venta_id:uuid.UUID,user:Usuario=Depends(require_roles(RolesSistema.CLIENTE)),db:Session=Depends(get_db)):
    venta=db.scalar(select(Venta).options(joinedload(Venta.detalles),joinedload(Venta.cliente)).where(Venta.id==venta_id))
    if not venta or venta.cliente_id!=user.cliente_id: raise NotFoundException('Comprobante no encontrado')
    out=io.BytesIO();pdf=canvas.Canvas(out,pagesize=A4);y=800
    pdf.setFont('Helvetica-Bold',16);pdf.drawString(50,y,'Salón de Belleza - Comprobante');y-=30
    pdf.setFont('Helvetica',10);pdf.drawString(50,y,f'Número: {venta.numero_comprobante}');y-=18
    pdf.drawString(50,y,f'Cliente: {venta.cliente.nombre_completo if venta.cliente else "Consumidor final"}');y-=18
    pdf.drawString(50,y,f'Fecha: {venta.fecha}');y-=30
    for d in venta.detalles:
      nombre=d.producto.nombre if d.producto_id and d.producto else (d.servicio.nombre if d.servicio else 'Ítem')
      pdf.drawString(50,y,f'{d.cantidad} x {nombre} - S/ {d.subtotal}');y-=18
    y-=10;pdf.setFont('Helvetica-Bold',12);pdf.drawString(50,y,f'TOTAL: S/ {venta.total}')
    pdf.save();return Response(out.getvalue(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename={venta.numero_comprobante}.pdf'})

from app.models.online_order_model import PedidoOnline, PedidoOnlineDetalle

ESTADOS_PEDIDO_ONLINE = ['PENDIENTE','CONFIRMADO','LISTO','ENTREGADO','CANCELADO']
TRANSICIONES_PEDIDO_ONLINE = {
    'PENDIENTE': {'CONFIRMADO','CANCELADO'},
    'CONFIRMADO': {'LISTO','CANCELADO'},
    'LISTO': {'ENTREGADO','CANCELADO'},
    'ENTREGADO': set(),
    'CANCELADO': set(),
}

def _pedido_staff_response(p):
    return {'id':str(p.id),'codigo':p.codigo,'estado':p.estado,'cliente_id':str(p.cliente_id),
      'cliente_nombre':p.cliente.nombre_completo,'subtotal':p.subtotal,'descuento':p.descuento,'total':p.total,
      'modalidad_entrega':p.modalidad_entrega,'direccion_entrega':p.direccion_entrega,'metodo_pago':p.metodo_pago,
      'notas':p.notas,'fecha':p.fecha,
      'items':[{'producto_id':str(d.producto_id),'nombre':d.producto.nombre,'cantidad':d.cantidad,
        'precio_unitario':d.precio_unitario,'subtotal':d.subtotal} for d in p.detalles]}

@router.get('/online-orders')
def listar_pedidos_online(estado:str|None=Query(None),
    user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA)),db:Session=Depends(get_db)):
    q=select(PedidoOnline).options(joinedload(PedidoOnline.cliente),
      joinedload(PedidoOnline.detalles).joinedload(PedidoOnlineDetalle.producto)).order_by(PedidoOnline.fecha.desc())
    if estado:q=q.where(PedidoOnline.estado==estado)
    items=list(db.scalars(q).unique())
    return {"data":{"items":[_pedido_staff_response(x) for x in items],
      "pendientes":sum(1 for x in items if x.estado in ('PENDIENTE','CONFIRMADO','LISTO'))}}

@router.patch('/online-orders/{pedido_id}/status')
def cambiar_estado_pedido_online(pedido_id:uuid.UUID,estado:str=Query(...),
    user:Usuario=Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA)),db:Session=Depends(get_db)):
    if estado not in ESTADOS_PEDIDO_ONLINE: raise ConflictException('Estado inválido')
    p=db.query(PedidoOnline).options(joinedload(PedidoOnline.cliente),
      joinedload(PedidoOnline.detalles).joinedload(PedidoOnlineDetalle.producto)).filter(PedidoOnline.id==pedido_id).first()
    if not p: raise NotFoundException('Pedido no encontrado')
    if estado not in TRANSICIONES_PEDIDO_ONLINE.get(p.estado,set()):
        raise ConflictException(f'No se puede cambiar un pedido de {p.estado} a {estado}')
    anterior=p.estado;p.estado=estado
    registrar_auditoria(db,user.id,AccionAuditoria.EDITAR,'PEDIDOS_ONLINE','PedidoOnline',str(p.id),{"estado":anterior},{"estado":estado})
    db.commit();return {"message":"Estado del pedido actualizado","data":_pedido_staff_response(p)}

@router.get('/notifications')
def notificaciones(user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    items=list(db.scalars(select(Notificacion).where(Notificacion.usuario_id==user.id).order_by(Notificacion.fecha.desc()).limit(50)))
    return {"data":[{"id":str(x.id),"titulo":x.titulo,"mensaje":x.mensaje,"tipo":x.tipo,"leida":x.leida,"fecha":x.fecha} for x in items]}

@router.patch('/notifications/{notification_id}/read')
def leer_notificacion(notification_id:uuid.UUID,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    n=db.get(Notificacion,notification_id)
    if not n or n.usuario_id!=user.id: raise NotFoundException('Notificación no encontrada')
    n.leida=True;db.commit();return {"message":"Notificación marcada como leída"}
