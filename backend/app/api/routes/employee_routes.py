"""Rutas REST del módulo de empleados."""
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.database.session import get_db
from app.models.employee_model import Empleado
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaMensaje, RespuestaPaginada
from app.schemas.employee_schema import (
    EmpleadoCrearRequest, EmpleadoActualizarRequest, EmpleadoCambiarEstadoRequest,
    EmpleadoResponse, ServicioEmpleadoResponse, HorarioEmpleadoRequest,
    HorarioEmpleadoResponse, VacacionEmpleadoCrearRequest, VacacionEmpleadoResponse,
    BloqueoHorarioCrearRequest, BloqueoHorarioResponse,
)
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Empleados"], dependencies=[Depends(require_roles(
    RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA, RolesSistema.ESTILISTA))])


def _response(e: Empleado) -> EmpleadoResponse:
    return EmpleadoResponse(
        id=e.id, usuario_id=e.usuario_id, nombres=e.nombres, apellidos=e.apellidos,
        nombre_completo=e.nombre_completo, documento=e.documento, telefono=e.telefono,
        correo=e.correo, cargo=e.cargo, especialidad=e.especialidad, salario=e.salario,
        porcentaje_comision_default=e.porcentaje_comision_default,
        fecha_ingreso=e.fecha_ingreso, estado=e.estado,
        servicios=[ServicioEmpleadoResponse(id=x.servicio.id, nombre=x.servicio.nombre,
                    precio=x.servicio.precio, duracion_minutos=x.servicio.duracion_minutos)
                   for x in e.servicios], created_at=e.created_at, updated_at=e.updated_at)


@router.get("", response_model=RespuestaPaginada[EmpleadoResponse])
def listar_empleados(estado: str | None = Query(None), cargo: str | None = Query(None),
    busqueda: str | None = Query(None), pagina: int = Query(1, ge=1),
    tamano_pagina: int = Query(20, ge=1, le=100), orden_por: str | None = Query("created_at"),
    orden_direccion: str = Query("desc", pattern="^(asc|desc)$"), db: Session = Depends(get_db)):
    items,total=EmployeeService(db).listar(estado,cargo,busqueda,pagina,tamano_pagina,orden_por,orden_direccion)
    return RespuestaPaginada.crear([_response(x) for x in items],total,pagina,tamano_pagina)


@router.post("", response_model=RespuestaExito[EmpleadoResponse], status_code=201,
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def crear_empleado(datos: EmpleadoCrearRequest, actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    return RespuestaExito(data=_response(EmployeeService(db).crear(datos,actor)),message="Empleado creado correctamente")


@router.get("/{empleado_id}", response_model=RespuestaExito[EmpleadoResponse])
def obtener_empleado(empleado_id: uuid.UUID, db: Session=Depends(get_db)):
    return RespuestaExito(data=_response(EmployeeService(db).obtener(empleado_id)))


@router.put("/{empleado_id}", response_model=RespuestaExito[EmpleadoResponse],
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def actualizar_empleado(empleado_id: uuid.UUID, datos: EmpleadoActualizarRequest,
 actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    return RespuestaExito(data=_response(EmployeeService(db).actualizar(empleado_id,datos,actor)),message="Empleado actualizado correctamente")


@router.patch("/{empleado_id}/status", response_model=RespuestaExito[EmpleadoResponse],
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def cambiar_estado(empleado_id: uuid.UUID, datos: EmpleadoCambiarEstadoRequest,
 actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    return RespuestaExito(data=_response(EmployeeService(db).cambiar_estado(empleado_id,datos.estado,actor)),message="Estado actualizado")


@router.delete("/{empleado_id}", response_model=RespuestaMensaje,
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_empleado(empleado_id: uuid.UUID, actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    EmployeeService(db).eliminar(empleado_id,actor); return RespuestaMensaje(message="Empleado inactivado correctamente")


@router.put("/{empleado_id}/schedule/{dia_semana}", response_model=RespuestaExito[HorarioEmpleadoResponse],
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA))])
def guardar_horario(empleado_id: uuid.UUID, dia_semana: int, datos: HorarioEmpleadoRequest,
 actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    datos.dia_semana=dia_semana
    return RespuestaExito(data=EmployeeService(db).guardar_horario(empleado_id,datos,actor),message="Horario guardado")


@router.post("/{empleado_id}/vacations", response_model=RespuestaExito[VacacionEmpleadoResponse], status_code=201,
 dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA))])
def agregar_vacacion(empleado_id: uuid.UUID, datos: VacacionEmpleadoCrearRequest,
 actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    return RespuestaExito(data=EmployeeService(db).agregar_vacacion(empleado_id,datos,actor),message="Vacación registrada")


@router.post("/{empleado_id}/blocks", response_model=RespuestaExito[BloqueoHorarioResponse], status_code=201)
def agregar_bloqueo(empleado_id: uuid.UUID, datos: BloqueoHorarioCrearRequest,
 actor: Usuario=Depends(get_current_user), db: Session=Depends(get_db)):
    return RespuestaExito(data=EmployeeService(db).agregar_bloqueo(empleado_id,datos,actor),message="Bloqueo registrado")
