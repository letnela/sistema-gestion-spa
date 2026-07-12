"""
Rutas REST del módulo de gestión de usuarios.
Todas las operaciones de este módulo están restringidas al rol ADMINISTRADOR,
según lo especificado en las reglas de negocio del sistema.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.database.session import get_db
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaPaginada
from app.schemas.user_schema import (
    UsuarioActualizarRequest,
    UsuarioCambiarEstadoRequest,
    UsuarioCambiarRolRequest,
    UsuarioCrearRequest,
    UsuarioResponse,
    UsuarioRestablecerPasswordResponse,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
    dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))],
)


def _a_response(usuario: Usuario) -> UsuarioResponse:
    """Convierte una entidad Usuario del ORM a su schema de respuesta."""
    return UsuarioResponse(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        rol=usuario.rol.nombre,
        estado=usuario.estado,
        telefono=usuario.telefono,
        avatar_url=usuario.avatar_url,
        ultimo_login=usuario.ultimo_login,
        debe_cambiar_password=usuario.debe_cambiar_password,
        created_at=usuario.created_at,
    )


@router.get("", response_model=RespuestaPaginada[UsuarioResponse], summary="Listar usuarios")
def listar_usuarios(
    rol: str | None = Query(default=None, description="Filtrar por rol"),
    estado: str | None = Query(default=None, description="Filtrar por estado"),
    busqueda: str | None = Query(default=None, description="Buscar por nombre o correo"),
    pagina: int = Query(default=1, ge=1),
    tamano_pagina: int = Query(default=20, ge=1, le=100),
    orden_por: str | None = Query(default="created_at"),
    orden_direccion: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> RespuestaPaginada[UsuarioResponse]:
    """Lista los usuarios del sistema con filtros, búsqueda, orden y paginación."""
    servicio = UserService(db)
    usuarios, total = servicio.listar(
        rol, estado, busqueda, pagina, tamano_pagina, orden_por, orden_direccion
    )
    return RespuestaPaginada.crear([_a_response(u) for u in usuarios], total, pagina, tamano_pagina)


@router.post("", response_model=RespuestaExito[UsuarioResponse], status_code=201, summary="Crear usuario")
def crear_usuario(
    datos: UsuarioCrearRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaExito[UsuarioResponse]:
    """Crea un nuevo usuario del sistema (administrador, recepcionista o estilista)."""
    servicio = UserService(db)
    usuario = servicio.crear(datos, current_user)
    return RespuestaExito(data=_a_response(usuario), message="Usuario creado correctamente")


@router.get("/{usuario_id}", response_model=RespuestaExito[UsuarioResponse], summary="Obtener usuario")
def obtener_usuario(usuario_id: uuid.UUID, db: Session = Depends(get_db)) -> RespuestaExito[UsuarioResponse]:
    """Obtiene el detalle de un usuario por su identificador."""
    servicio = UserService(db)
    usuario = servicio.obtener_por_id(usuario_id)
    return RespuestaExito(data=_a_response(usuario))


@router.put("/{usuario_id}", response_model=RespuestaExito[UsuarioResponse], summary="Editar usuario")
def actualizar_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioActualizarRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaExito[UsuarioResponse]:
    """Actualiza los datos editables de un usuario existente."""
    servicio = UserService(db)
    usuario = servicio.actualizar(usuario_id, datos, current_user)
    return RespuestaExito(data=_a_response(usuario), message="Usuario actualizado correctamente")


@router.patch(
    "/{usuario_id}/status", response_model=RespuestaExito[UsuarioResponse], summary="Activar/Inactivar usuario"
)
def cambiar_estado_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioCambiarEstadoRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaExito[UsuarioResponse]:
    """Activa o inactiva un usuario del sistema."""
    servicio = UserService(db)
    usuario = servicio.cambiar_estado(usuario_id, datos.estado, current_user)
    return RespuestaExito(data=_a_response(usuario), message=f"Usuario {datos.estado.lower()} correctamente")


@router.patch(
    "/{usuario_id}/role", response_model=RespuestaExito[UsuarioResponse], summary="Cambiar rol de usuario"
)
def cambiar_rol_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioCambiarRolRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaExito[UsuarioResponse]:
    """Cambia el rol asignado a un usuario del sistema."""
    servicio = UserService(db)
    usuario = servicio.cambiar_rol(usuario_id, datos.rol, current_user)
    return RespuestaExito(data=_a_response(usuario), message="Rol actualizado correctamente")


@router.patch(
    "/{usuario_id}/reset-password",
    response_model=RespuestaExito[UsuarioRestablecerPasswordResponse],
    summary="Restablecer contraseña de un usuario",
)
def restablecer_password_usuario(
    usuario_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaExito[UsuarioRestablecerPasswordResponse]:
    """Genera una contraseña temporal para el usuario indicado (uso administrativo)."""
    servicio = UserService(db)
    password_temporal = servicio.restablecer_password(usuario_id, current_user)
    return RespuestaExito(
        data=UsuarioRestablecerPasswordResponse(password_temporal=password_temporal),
        message="Contraseña restablecida correctamente",
    )
