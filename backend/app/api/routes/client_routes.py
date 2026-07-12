"""Rutas REST de clientes y sus accesos al portal."""
import uuid
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.database.session import get_db
from app.models.client_model import Cliente
from app.models.user_model import Usuario
from app.schemas.client_schema import (ClienteActualizarRequest,ClienteCambiarEstadoRequest,ClienteCrearRequest,
    ClientePortalCrearRequest,ClientePortalEstadoRequest,ClientePortalAccesoResponse,ClienteResponse)
from app.schemas.common_schema import RespuestaExito,RespuestaMensaje,RespuestaPaginada
from app.services.client_service import ClientService

router=APIRouter(prefix="/clients",tags=["Clientes"],dependencies=[Depends(require_roles(
    RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA,RolesSistema.ESTILISTA))])

def _response(c:Cliente,db:Session)->ClienteResponse:
    u=ClientService(db).usuario_portal(c.id)
    return ClienteResponse(id=c.id,nombres=c.nombres,apellidos=c.apellidos,nombre_completo=c.nombre_completo,
        documento=c.documento,telefono=c.telefono,correo=c.correo,direccion=c.direccion,
        fecha_nacimiento=c.fecha_nacimiento,observaciones=c.observaciones,preferencias=c.preferencias,
        alergias=c.alergias,estado=c.estado,created_at=c.created_at,updated_at=c.updated_at,
        usuario_id=u.id if u else None,portal_estado=u.estado if u else None,
        portal_ultimo_login=u.ultimo_login if u else None,
        portal_debe_cambiar_password=u.debe_cambiar_password if u else None)

@router.get("",response_model=RespuestaPaginada[ClienteResponse])
def listar_clientes(estado:str|None=Query(None),busqueda:str|None=Query(None),pagina:int=Query(1,ge=1),
    tamano_pagina:int=Query(20,ge=1,le=100),orden_por:str|None=Query("created_at"),
    orden_direccion:str=Query("desc",pattern="^(asc|desc)$"),db:Session=Depends(get_db)):
    items,total=ClientService(db).listar(estado,busqueda,pagina,tamano_pagina,orden_por,orden_direccion)
    return RespuestaPaginada.crear([_response(c,db) for c in items],total,pagina,tamano_pagina)

@router.post("",response_model=RespuestaExito[ClienteResponse],status_code=201,
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def crear_cliente(datos:ClienteCrearRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    c=ClientService(db).crear(datos,actor)
    return RespuestaExito(data=_response(c,db),message="Cliente creado correctamente")

@router.get("/{cliente_id}",response_model=RespuestaExito[ClienteResponse])
def obtener_cliente(cliente_id:uuid.UUID,db:Session=Depends(get_db)):
    return RespuestaExito(data=_response(ClientService(db).obtener_por_id(cliente_id),db))

@router.put("/{cliente_id}",response_model=RespuestaExito[ClienteResponse],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def actualizar_cliente(cliente_id:uuid.UUID,datos:ClienteActualizarRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=_response(ClientService(db).actualizar(cliente_id,datos,actor),db),message="Cliente actualizado correctamente")

@router.patch("/{cliente_id}/status",response_model=RespuestaExito[ClienteResponse],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def cambiar_estado(cliente_id:uuid.UUID,datos:ClienteCambiarEstadoRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=_response(ClientService(db).cambiar_estado(cliente_id,datos.estado,actor),db),message="Estado actualizado")

@router.post("/{cliente_id}/portal-access",response_model=RespuestaExito[ClientePortalAccesoResponse],status_code=201,
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def crear_portal(cliente_id:uuid.UUID,datos:ClientePortalCrearRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    u,pwd=ClientService(db).crear_acceso_portal(cliente_id,datos.password,actor)
    return RespuestaExito(data=ClientePortalAccesoResponse(usuario_id=u.id,correo=u.correo,estado=u.estado,
        password_temporal=pwd,debe_cambiar_password=u.debe_cambiar_password),message="Acceso al portal creado")

@router.patch("/{cliente_id}/portal-access/status",response_model=RespuestaExito[ClientePortalAccesoResponse],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def estado_portal(cliente_id:uuid.UUID,datos:ClientePortalEstadoRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    u=ClientService(db).cambiar_estado_portal(cliente_id,datos.estado,actor)
    return RespuestaExito(data=ClientePortalAccesoResponse(usuario_id=u.id,correo=u.correo,estado=u.estado,
        debe_cambiar_password=u.debe_cambiar_password),message="Acceso al portal actualizado")

@router.post("/{cliente_id}/portal-access/reset-password",response_model=RespuestaExito[ClientePortalAccesoResponse],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])
def reset_portal(cliente_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    u,pwd=ClientService(db).resetear_password_portal(cliente_id,actor)
    return RespuestaExito(data=ClientePortalAccesoResponse(usuario_id=u.id,correo=u.correo,estado=u.estado,
        password_temporal=pwd,debe_cambiar_password=True),message="Contraseña temporal generada")

@router.delete("/{cliente_id}/portal-access",response_model=RespuestaMensaje,
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def borrar_portal(cliente_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    ClientService(db).eliminar_acceso_portal(cliente_id,actor)
    return RespuestaMensaje(message="Acceso al portal eliminado")

@router.delete("/{cliente_id}",response_model=RespuestaMensaje,dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_cliente(cliente_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    ClientService(db).eliminar(cliente_id,actor); return RespuestaMensaje(message="Cliente archivado correctamente")
