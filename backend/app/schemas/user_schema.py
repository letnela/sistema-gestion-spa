"""Schemas de Pydantic para el módulo de gestión de usuarios."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import EstadoGenerico, RolesSistema


class UsuarioCrearRequest(BaseModel):
    """Datos de entrada para crear un nuevo usuario del sistema."""

    nombre_completo: str = Field(min_length=3, max_length=150)
    correo: EmailStr
    password: str = Field(min_length=8)
    rol: str
    telefono: str | None = Field(default=None, max_length=30)

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, valor: str) -> str:
        """Valida que el rol pertenezca al conjunto de roles permitidos."""
        if valor not in RolesSistema.TODOS:
            raise ValueError(f"Rol inválido. Debe ser uno de: {RolesSistema.TODOS}")
        return valor

    @field_validator("password")
    @classmethod
    def validar_fortaleza(cls, valor: str) -> str:
        """Valida que la contraseña tenga al menos una letra y un número."""
        if not any(c.isdigit() for c in valor):
            raise ValueError("La contraseña debe contener al menos un número")
        if not any(c.isalpha() for c in valor):
            raise ValueError("La contraseña debe contener al menos una letra")
        return valor


class UsuarioActualizarRequest(BaseModel):
    """Datos de entrada para actualizar un usuario existente. Todos los campos son opcionales."""

    nombre_completo: str | None = Field(default=None, min_length=3, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = None


class UsuarioCambiarRolRequest(BaseModel):
    """Datos de entrada para cambiar el rol de un usuario."""

    rol: str

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, valor: str) -> str:
        """Valida que el rol pertenezca al conjunto de roles permitidos."""
        if valor not in RolesSistema.TODOS:
            raise ValueError(f"Rol inválido. Debe ser uno de: {RolesSistema.TODOS}")
        return valor


class UsuarioCambiarEstadoRequest(BaseModel):
    """Datos de entrada para activar o inactivar un usuario."""

    estado: str

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor: str) -> str:
        """Valida que el estado pertenezca al conjunto de estados permitidos."""
        if valor not in EstadoGenerico.TODOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {EstadoGenerico.TODOS}")
        return valor


class UsuarioRestablecerPasswordResponse(BaseModel):
    """Respuesta al restablecer la contraseña de un usuario desde administración."""

    password_temporal: str
    mensaje: str = "Contraseña restablecida. El usuario deberá cambiarla en su próximo inicio de sesión."


class UsuarioResponse(BaseModel):
    """Representación de salida de un usuario del sistema."""

    id: uuid.UUID
    nombre_completo: str
    correo: EmailStr
    rol: str
    estado: str
    telefono: str | None = None
    avatar_url: str | None = None
    ultimo_login: datetime | None = None
    debe_cambiar_password: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioFiltros(BaseModel):
    """Filtros disponibles para el listado de usuarios."""

    rol: str | None = None
    estado: str | None = None
    busqueda: str | None = None
