"""
Dependencias globales de FastAPI.
Provee `get_current_user`, usada por todos los routers protegidos para
obtener el usuario autenticado a partir del token JWT en el header Authorization.
"""
import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.constants import EstadoGenerico
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user_model import Usuario
from app.repositories.implementations.usuario_repository import UsuarioRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Extrae y valida el token JWT del header Authorization, y retorna el
    usuario autenticado correspondiente. Lanza UnauthorizedException si el
    token falta, es inválido, expiró, o el usuario ya no existe o está inactivo.
    """
    if credentials is None:
        raise UnauthorizedException("No se proporcionó un token de autenticación")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise UnauthorizedException("El token de autenticación es inválido o expiró") from exc

    if payload.get("type") != "access":
        raise UnauthorizedException("El token proporcionado no es un token de acceso")

    try:
        usuario_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedException("El token de autenticación tiene un formato inválido") from exc

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.obtener_por_id(usuario_id)

    if not usuario:
        raise UnauthorizedException("El usuario asociado al token ya no existe")
    if usuario.estado != EstadoGenerico.ACTIVO:
        raise UnauthorizedException("El usuario se encuentra inactivo")

    return usuario


def obtener_ip_cliente(request: Request) -> str | None:
    """Extrae la IP real del cliente, considerando el header X-Forwarded-For si existe."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def obtener_navegador_cliente(request: Request) -> str | None:
    """Extrae el User-Agent del cliente para fines de auditoría."""
    return request.headers.get("user-agent")
