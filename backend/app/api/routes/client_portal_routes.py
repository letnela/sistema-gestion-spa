import uuid
from datetime import date
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db,get_current_user
from app.core.constants import RolesSistema,EstadoCita
from app.core.permissions import require_roles
from app.core.exceptions import UnauthorizedException,ConflictException
from app.models.user_model import Usuario
from app.models.client_model import Cliente
from app.models.employee_model import Empleado, EmpleadoServicio
from app.models.service_model import Servicio
from app.models.promotion_model import Promocion
from app.schemas.common_schema import RespuestaExito,RespuestaMensaje,RespuestaPaginada
from app.schemas.auth_schema import PerfilClienteActualizarRequest,UsuarioPerfilResponse
from app.schemas.client_portal_schema import PortalCitaCrearRequest,PortalCitaReprogramarRequest,PortalCancelarRequest
from app.schemas.appointment_schema import CitaCrearRequest,CitaActualizarRequest,CitaResponse,CitaServicioResponse
from app.services.appointment_service import AppointmentService
router=APIRouter(prefix="/client-portal",tags=["Portal del cliente"],dependencies=[Depends(require_roles(RolesSistema.CLIENTE))])
def _cliente(user):
    if not user.cliente_id: raise UnauthorizedException("La cuenta no está vinculada a un cliente")
    return user.cliente_id
def _response(c):
    return CitaResponse(id=c.id,cliente_id=c.cliente_id,cliente_nombre=c.cliente.nombre_completo,empleado_id=c.empleado_id,empleado_nombre=c.empleado.nombre_completo,fecha=c.fecha,hora_inicio=c.hora_inicio,hora_fin=c.hora_fin,duracion_total_minutos=c.duracion_total_minutos,precio_total=c.precio_total,estado=c.estado,notas=c.notas,motivo_cancelacion=c.motivo_cancelacion,servicios=[CitaServicioResponse(id=x.id,servicio_id=x.servicio_id,nombre=x.servicio.nombre,precio_aplicado=x.precio_aplicado,duracion_aplicada_minutos=x.duracion_aplicada_minutos) for x in c.servicios],created_at=c.created_at,updated_at=c.updated_at)
@router.get("/profile")
def perfil(user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    c=db.query(Cliente).filter(Cliente.id==_cliente(user)).first(); return RespuestaExito(data={"id":str(c.id),"nombres":c.nombres,"apellidos":c.apellidos,"correo":c.correo,"telefono":c.telefono,"documento":c.documento,"direccion":c.direccion,"fecha_nacimiento":c.fecha_nacimiento,"preferencias":c.preferencias,"alergias":c.alergias})
@router.put("/profile")
def editar_perfil(datos:PerfilClienteActualizarRequest,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    c=db.query(Cliente).filter(Cliente.id==_cliente(user)).first()
    for k,v in datos.model_dump(exclude_unset=True).items(): setattr(c,k,v)
    user.nombre_completo=f"{c.nombres} {c.apellidos}"; user.telefono=c.telefono; db.commit(); return RespuestaMensaje(message="Perfil actualizado")


@router.get("/home")
def inicio_cliente(user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    cliente_id=_cliente(user)
    svc=AppointmentService(db)
    items,total=svc.listar(None,None,None,cliente_id,None,None,1,100,"fecha","asc")
    hoy=date.today()
    proximas=[x for x in items if x.fecha>=hoy and x.estado not in [EstadoCita.CANCELADA,EstadoCita.NO_ASISTIO]][:3]
    return RespuestaExito(data={
        "proximas_citas":[_response(x) for x in proximas],
        "total_citas":total,
        "pendientes":sum(1 for x in items if x.estado in [EstadoCita.PENDIENTE,EstadoCita.CONFIRMADA]),
        "finalizadas":sum(1 for x in items if x.estado==EstadoCita.FINALIZADA)
    })

@router.get("/catalog/promotions")
def promociones_cliente(db:Session=Depends(get_db)):
    hoy=date.today()
    items=db.query(Promocion).options(joinedload(Promocion.servicios)).filter(
        Promocion.activa.is_(True),Promocion.fecha_inicio<=hoy,Promocion.fecha_fin>=hoy
    ).order_by(Promocion.fecha_fin).all()
    return RespuestaExito(data=[{
        "id":str(x.id),"nombre":x.nombre,"descripcion":x.descripcion,
        "porcentaje_descuento":x.porcentaje_descuento,"fecha_fin":x.fecha_fin,
        "servicio_ids":[str(y.servicio_id) for y in x.servicios]
    } for x in items])

@router.get("/catalog/services")
def catalogo_servicios(db:Session=Depends(get_db)):
    items=db.query(Servicio).filter(Servicio.estado=="ACTIVO").order_by(Servicio.nombre).all()
    return RespuestaExito(data=[{"id":str(x.id),"nombre":x.nombre,"descripcion":x.descripcion,"precio":x.precio,"duracion_minutos":x.duracion_minutos,"imagen_url":x.imagen_url,"categoria_id":str(x.categoria_id),"categoria_nombre":x.categoria.nombre if x.categoria else None} for x in items])

@router.get("/catalog/employees")
def catalogo_empleados(servicio_ids:list[uuid.UUID]=Query(default=[]),db:Session=Depends(get_db)):
    q=db.query(Empleado).filter(Empleado.estado=="ACTIVO")
    empleados=q.order_by(Empleado.nombres,Empleado.apellidos).all()
    if servicio_ids:
        requeridos=set(servicio_ids)
        empleados=[e for e in empleados if requeridos.issubset({x.servicio_id for x in e.servicios})]
    return RespuestaExito(data=[{"id":str(x.id),"nombre_completo":x.nombre_completo,"especialidad":x.especialidad} for x in empleados])

@router.get("/catalog/available-slots")
def horarios_cliente(empleado_id:uuid.UUID,fecha:date,servicio_ids:list[uuid.UUID]=Query(...),cita_id:uuid.UUID|None=Query(None),user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    svc=AppointmentService(db)
    if cita_id is not None:
        cita=svc.obtener(cita_id)
        if cita.cliente_id!=_cliente(user): raise UnauthorizedException("No puede consultar horarios de esta cita")
    return RespuestaExito(data=svc.horarios_disponibles(empleado_id,fecha,servicio_ids,excluir_cita_id=cita_id))

@router.get("/appointments",response_model=RespuestaPaginada[CitaResponse])
def mis_citas(pagina:int=Query(1,ge=1),tamano_pagina:int=Query(20,ge=1,le=100),user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    items,total=AppointmentService(db).listar(None,None,None,_cliente(user),None,None,pagina,tamano_pagina,"fecha","desc")
    return RespuestaPaginada.crear([_response(x) for x in items],total,pagina,tamano_pagina)
@router.post("/appointments",response_model=RespuestaExito[CitaResponse],status_code=201)
def crear_cita(datos:PortalCitaCrearRequest,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    req=CitaCrearRequest(cliente_id=_cliente(user),**datos.model_dump()); return RespuestaExito(data=_response(AppointmentService(db).crear(req,user)),message="Cita reservada")
@router.put("/appointments/{cita_id}",response_model=RespuestaExito[CitaResponse])
def reprogramar(cita_id:uuid.UUID,datos:PortalCitaReprogramarRequest,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    svc=AppointmentService(db); cita=svc.obtener(cita_id)
    if cita.cliente_id!=_cliente(user): raise UnauthorizedException("No puede modificar esta cita")
    if cita.estado not in [EstadoCita.PENDIENTE,EstadoCita.CONFIRMADA]: raise ConflictException("La cita ya no puede reprogramarse")
    req=CitaActualizarRequest(**datos.model_dump(exclude_unset=True)); return RespuestaExito(data=_response(svc.actualizar(cita_id,req,user)),message="Cita reprogramada")
@router.patch("/appointments/{cita_id}/cancel",response_model=RespuestaExito[CitaResponse])
def cancelar(cita_id:uuid.UUID,datos:PortalCancelarRequest,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    svc=AppointmentService(db); cita=svc.obtener(cita_id)
    if cita.cliente_id!=_cliente(user): raise UnauthorizedException("No puede cancelar esta cita")
    return RespuestaExito(data=_response(svc.cambiar_estado(cita_id,EstadoCita.CANCELADA,datos.motivo,user)),message="Cita cancelada")

# Fase 21: tienda del cliente
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.models.product_model import Producto
from app.models.online_order_model import PedidoOnline, PedidoOnlineDetalle

class PedidoItemRequest(BaseModel):
    producto_id: uuid.UUID
    cantidad: int = Field(ge=1, le=20)

class PedidoCrearRequest(BaseModel):
    items: list[PedidoItemRequest] = Field(min_length=1)
    modalidad_entrega: str = 'RECOJO_SALON'
    direccion_entrega: str | None = Field(default=None, max_length=300)
    metodo_pago: str = 'PAGO_EN_SALON'
    notas: str | None = Field(default=None, max_length=500)

@router.get('/catalog/products')
def catalogo_productos(db:Session=Depends(get_db)):
    items=db.query(Producto).filter(Producto.estado=='ACTIVO',Producto.stock>0).order_by(Producto.nombre).all()
    return RespuestaExito(data=[{
      'id':str(x.id),'codigo':x.codigo,'nombre':x.nombre,'marca':x.marca,'descripcion':x.descripcion,
      'precio':x.precio_venta,'stock':x.stock,'imagen_url':x.imagen_url,
      'categoria_id':str(x.categoria_id),'categoria_nombre':x.categoria.nombre if x.categoria else None
    } for x in items])

def _pedido_response(p):
    return {'id':str(p.id),'codigo':p.codigo,'estado':p.estado,'subtotal':p.subtotal,'descuento':p.descuento,
      'total':p.total,'modalidad_entrega':p.modalidad_entrega,'direccion_entrega':p.direccion_entrega,
      'metodo_pago':p.metodo_pago,'notas':p.notas,'fecha':p.fecha,
      'items':[{'producto_id':str(d.producto_id),'nombre':d.producto.nombre,'imagen_url':d.producto.imagen_url,
        'cantidad':d.cantidad,'precio_unitario':d.precio_unitario,'subtotal':d.subtotal} for d in p.detalles]}

@router.post('/orders',status_code=201)
def crear_pedido(datos:PedidoCrearRequest,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    cliente_id=_cliente(user)
    cantidades={x.producto_id:x.cantidad for x in datos.items}
    productos=list(db.scalars(select(Producto).where(Producto.id.in_(cantidades.keys()))))
    if len(productos)!=len(cantidades): raise ConflictException('Uno o más productos no existen')
    subtotal=Decimal('0'); detalles=[]
    for p in productos:
      cantidad=cantidades[p.id]
      if p.estado!='ACTIVO' or p.stock<cantidad: raise ConflictException(f'Stock insuficiente para {p.nombre}')
      line=Decimal(p.precio_venta)*cantidad; subtotal+=line
      detalles.append((p,cantidad,line))
    codigo=f'WEB-{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}-{str(uuid.uuid4())[:4].upper()}'
    pedido=PedidoOnline(cliente_id=cliente_id,codigo=codigo,subtotal=subtotal,descuento=Decimal('0'),total=subtotal,
      modalidad_entrega=datos.modalidad_entrega,direccion_entrega=datos.direccion_entrega,
      metodo_pago=datos.metodo_pago,notas=datos.notas,estado='PENDIENTE')
    db.add(pedido);db.flush()
    for p,cantidad,line in detalles:
      db.add(PedidoOnlineDetalle(pedido_id=pedido.id,producto_id=p.id,cantidad=cantidad,precio_unitario=p.precio_venta,subtotal=line))
    db.commit();db.refresh(pedido)
    pedido=db.query(PedidoOnline).options(joinedload(PedidoOnline.detalles).joinedload(PedidoOnlineDetalle.producto)).filter(PedidoOnline.id==pedido.id).first()
    return RespuestaExito(data=_pedido_response(pedido),message='Pedido registrado. El salón confirmará la preparación.')

@router.get('/orders')
def mis_pedidos(user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    items=db.query(PedidoOnline).options(joinedload(PedidoOnline.detalles).joinedload(PedidoOnlineDetalle.producto)).filter(
      PedidoOnline.cliente_id==_cliente(user)).order_by(PedidoOnline.fecha.desc()).all()
    return RespuestaExito(data=[_pedido_response(x) for x in items])

@router.patch('/orders/{pedido_id}/cancel')
def cancelar_pedido(pedido_id:uuid.UUID,user:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    p=db.query(PedidoOnline).filter(PedidoOnline.id==pedido_id,PedidoOnline.cliente_id==_cliente(user)).first()
    if not p: raise ConflictException('Pedido no encontrado')
    if p.estado not in ['PENDIENTE','CONFIRMADO']: raise ConflictException('El pedido ya no puede cancelarse')
    p.estado='CANCELADO';db.commit();return RespuestaMensaje(message='Pedido cancelado')
