"""
Sistema de permisos por rol.
Define, mediante decoradores de dependencia de FastAPI, qué roles pueden
acceder a cada endpoint. Se usa en conjunto con app.api.dependencies.
"""
from typing import Callable, Iterable

from fastapi import Depends

from app.core.constants import RolesSistema
from app.core.exceptions import ForbiddenException
from app.models.user_model import Usuario


def require_roles(*roles_permitidos: str) -> Callable:
    """
    Crea una dependencia de FastAPI que valida que el usuario autenticado
    tenga uno de los roles permitidos.

    Uso:
        @router.get("/", dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
    """
    from app.api.dependencies import get_current_user  # import diferido para evitar ciclos

    def dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol.nombre not in roles_permitidos:
            raise ForbiddenException(
                f"El rol '{current_user.rol.nombre}' no tiene acceso a este recurso"
            )
        return current_user

    return dependency


def is_admin(current_user: Usuario) -> bool:
    """Retorna True si el usuario tiene rol de administrador."""
    return current_user.rol.nombre == RolesSistema.ADMINISTRADOR


def is_recepcionista(current_user: Usuario) -> bool:
    """Retorna True si el usuario tiene rol de recepcionista."""
    return current_user.rol.nombre == RolesSistema.RECEPCIONISTA


def is_estilista(current_user: Usuario) -> bool:
    """Retorna True si el usuario tiene rol de estilista."""
    return current_user.rol.nombre == RolesSistema.ESTILISTA


def has_any_role(current_user: Usuario, roles: Iterable[str]) -> bool:
    """Retorna True si el usuario tiene alguno de los roles indicados."""
    return current_user.rol.nombre in roles
