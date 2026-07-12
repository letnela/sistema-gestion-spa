"""Rutas REST de agenda y citas con alcance y acciones por rol."""
import uuid
from datetime import date, time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.core.constants import RolesSistema, EstadoCita
from app.core.exceptions import ForbiddenException, ConflictException
from app.core.permissions import require_roles
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaMensaje, RespuestaPaginada
from app.schemas.appointment_schema import *
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Citas"], dependencies=[Depends(require_roles(
    RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA, RolesSistema.ESTILISTA
))])


def _response(c):
    return CitaResponse(
        id=c.id, cliente_id=c.cliente_id, cliente_nombre=c.cliente.nombre_completo,
        empleado_id=c.empleado_id, empleado_nombre=c.empleado.nombre_completo, fecha=c.fecha,
        hora_inicio=c.hora_inicio, hora_fin=c.hora_fin,
        duracion_total_minutos=c.duracion_total_minutos, precio_total=c.precio_total,
        estado=c.estado, notas=c.notas, motivo_cancelacion=c.motivo_cancelacion,
        servicios=[CitaServicioResponse(id=x.id, servicio_id=x.servicio_id,
            nombre=x.servicio.nombre, precio_aplicado=x.precio_aplicado,
            duracion_aplicada_minutos=x.duracion_aplicada_minutos) for x in c.servicios],
        created_at=c.created_at, updated_at=c.updated_at,
    )


def _empleado_actor(actor: Usuario):
    if actor.rol.nombre != RolesSistema.ESTILISTA:
        return None
    if not actor.empleado:
        raise ForbiddenException("La cuenta de estilista no está vinculada a un empleado")
    return actor.empleado.id


@router.get("", response_model=RespuestaPaginada[CitaResponse])
def listar(fecha_desde: date | None = Query(None), fecha_hasta: date | None = Query(None),
    empleado_id: uuid.UUID | None = Query(None), cliente_id: uuid.UUID | None = Query(None),
    estado: str | None = Query(None), busqueda: str | None = Query(None),
    pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=100),
    orden_por: str = Query("fecha"), orden_direccion: str = Query("asc", pattern="^(asc|desc)$"),
    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    empleado_propio = _empleado_actor(actor)
    if empleado_propio:
        empleado_id = empleado_propio
        cliente_id = None
    items, total = AppointmentService(db).listar(fecha_desde, fecha_hasta, empleado_id,
        cliente_id, estado, busqueda, pagina, tamano_pagina, orden_por, orden_direccion)
    return RespuestaPaginada.crear([_response(x) for x in items], total, pagina, tamano_pagina)


@router.get("/summary", response_model=RespuestaExito[ResumenAgendaResponse])
def resumen(fecha: date = Query(...), actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    empleado_id = _empleado_actor(actor)
    return RespuestaExito(data=AppointmentService(db).resumen(fecha, empleado_id))


@router.get("/available-slots", response_model=RespuestaExito[list[HorarioDisponibleResponse]])
def horarios_disponibles(empleado_id: uuid.UUID, fecha: date, servicio_ids: list[uuid.UUID] = Query(...),
    cita_id: uuid.UUID | None = Query(None),
    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    empleado_propio = _empleado_actor(actor)
    if empleado_propio and empleado_id != empleado_propio:
        raise ForbiddenException("El estilista solo puede consultar su propia disponibilidad")
    return RespuestaExito(data=AppointmentService(db).horarios_disponibles(empleado_id, fecha, servicio_ids, excluir_cita_id=cita_id))


@router.get("/availability", response_model=RespuestaExito[DisponibilidadResponse])
def disponibilidad(empleado_id: uuid.UUID, fecha: date, hora_inicio: time, hora_fin: time,
    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    empleado_propio = _empleado_actor(actor)
    if empleado_propio and empleado_id != empleado_propio:
        raise ForbiddenException("El estilista solo puede consultar su propia disponibilidad")
    disponible, motivo = AppointmentService(db).verificar_disponibilidad(empleado_id, fecha, hora_inicio, hora_fin)
    return RespuestaExito(data=DisponibilidadResponse(disponible=disponible, empleado_id=empleado_id,
        fecha=fecha, hora_inicio=hora_inicio, hora_fin=hora_fin, motivo=motivo))


@router.post("", response_model=RespuestaExito[CitaResponse], status_code=201,
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA))])
def crear(datos: CitaCrearRequest, actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return RespuestaExito(data=_response(AppointmentService(db).crear(datos, actor)),
                          message="Cita creada correctamente")


@router.get("/{cita_id}", response_model=RespuestaExito[CitaResponse])
def obtener(cita_id: uuid.UUID, actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    cita = AppointmentService(db).obtener(cita_id)
    empleado_propio = _empleado_actor(actor)
    if empleado_propio and cita.empleado_id != empleado_propio:
        raise ForbiddenException("El estilista no puede consultar una cita de otro empleado")
    return RespuestaExito(data=_response(cita))


@router.put("/{cita_id}", response_model=RespuestaExito[CitaResponse],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA))])
def actualizar(cita_id: uuid.UUID, datos: CitaActualizarRequest,
    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return RespuestaExito(data=_response(AppointmentService(db).actualizar(cita_id, datos, actor)),
                          message="Cita actualizada correctamente")


@router.patch("/{cita_id}/status", response_model=RespuestaExito[CitaResponse])
def estado(cita_id: uuid.UUID, datos: CitaCambiarEstadoRequest,
    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = AppointmentService(db)
    cita = svc.obtener(cita_id)
    rol = actor.rol.nombre
    if rol == RolesSistema.ESTILISTA:
        empleado_propio = _empleado_actor(actor)
        if cita.empleado_id != empleado_propio:
            raise ForbiddenException("El estilista no puede modificar una cita de otro empleado")
        permitidos = {
            EstadoCita.PENDIENTE: {EstadoCita.NO_ASISTIO},
            EstadoCita.CONFIRMADA: {EstadoCita.EN_PROCESO, EstadoCita.NO_ASISTIO},
            EstadoCita.EN_PROCESO: {EstadoCita.FINALIZADA},
        }
        if datos.estado not in permitidos.get(cita.estado, set()):
            raise ConflictException("El estilista solo puede iniciar, finalizar o marcar inasistencia")
    elif rol == RolesSistema.RECEPCIONISTA and datos.estado == EstadoCita.FINALIZADA:
        raise ForbiddenException("La recepcionista no puede finalizar servicios")
    return RespuestaExito(data=_response(svc.cambiar_estado(cita_id, datos.estado,
        datos.motivo_cancelacion, actor)), message="Estado actualizado")


@router.delete("/{cita_id}", response_model=RespuestaMensaje,
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar(cita_id: uuid.UUID, actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    AppointmentService(db).eliminar(cita_id, actor)
    return RespuestaMensaje(message="Cita eliminada correctamente")
