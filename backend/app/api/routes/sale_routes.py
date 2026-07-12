"""Rutas REST para ventas, pagos y caja."""
import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaPaginada
from app.schemas.sale_schema import *
from app.services.sale_service import SaleService

router=APIRouter(tags=["Ventas y Caja"])

def venta_response(v):
    detalles=[]
    for d in v.detalles:
        descripcion=d.producto.nombre if d.producto_id and d.producto else d.servicio.nombre
        detalles.append(VentaDetalleResponse(id=d.id,producto_id=d.producto_id,servicio_id=d.servicio_id,
            empleado_id=d.empleado_id,descripcion=descripcion,cantidad=d.cantidad,precio_unitario=d.precio_unitario,
            descuento=d.descuento,subtotal=d.subtotal))
    return VentaResponse(id=v.id,numero_comprobante=v.numero_comprobante,cliente_id=v.cliente_id,cita_id=v.cita_id,
        cliente_nombre=v.cliente.nombre_completo if v.cliente else None,usuario_id=v.usuario_id,
        subtotal=v.subtotal,descuento=v.descuento,impuesto=v.impuesto,total=v.total,estado=v.estado,
        motivo_anulacion=v.motivo_anulacion,fecha=v.fecha,detalles=detalles,pagos=v.pagos)

@router.get("/sales",response_model=RespuestaPaginada[VentaResponse])
def listar_ventas(fecha_desde:date|None=Query(None),fecha_hasta:date|None=Query(None),cliente_id:uuid.UUID|None=Query(None),
    estado:str|None=Query(None),busqueda:str|None=Query(None),pagina:int=Query(1,ge=1),tamano_pagina:int=Query(20,ge=1,le=100),
    orden_direccion:str=Query("desc",pattern="^(asc|desc)$"),db:Session=Depends(get_db),usuario:Usuario=Depends(get_current_user)):
    items,total=SaleService(db).listar(fecha_desde=fecha_desde,fecha_hasta=fecha_hasta,cliente_id=cliente_id,
        estado=estado,busqueda=busqueda,pagina=pagina,tamano_pagina=tamano_pagina,orden_direccion=orden_direccion)
    return RespuestaPaginada.crear([venta_response(x) for x in items],total,pagina,tamano_pagina)

@router.post("/sales",response_model=RespuestaExito[VentaResponse],status_code=201,
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def crear_venta(datos:VentaCrearRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=venta_response(SaleService(db).crear(datos,actor)),message="Venta registrada correctamente")

@router.get("/sales/{venta_id}",response_model=RespuestaExito[VentaResponse])
def obtener_venta(venta_id:uuid.UUID,db:Session=Depends(get_db),usuario:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=venta_response(SaleService(db).obtener(venta_id)))

@router.patch("/sales/{venta_id}/cancel",response_model=RespuestaExito[VentaResponse],
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def anular_venta(venta_id:uuid.UUID,datos:AnularVentaRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=venta_response(SaleService(db).anular(venta_id,datos.motivo,actor)),message="Venta anulada correctamente")
