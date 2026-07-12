"""Schemas de Pydantic para el módulo de autenticación."""
import uuid
from datetime import datetime, date

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Datos de entrada para iniciar sesión."""

    correo: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Respuesta con los tokens de acceso y refresco tras un login exitoso."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expira_en_minutos: int


class RefreshTokenRequest(BaseModel):
    """Datos de entrada para renovar un token de acceso."""

    refresh_token: str


class UsuarioPerfilResponse(BaseModel):
    """Datos del perfil del usuario autenticado."""

    id: uuid.UUID
    nombre_completo: str
    correo: EmailStr
    rol: str
    telefono: str | None = None
    avatar_url: str | None = None
    ultimo_login: datetime | None = None
    empleado_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class CambiarPasswordRequest(BaseModel):
    """Datos de entrada para que un usuario autenticado cambie su propia contraseña."""

    password_actual: str
    password_nuevo: str = Field(min_length=8)

    @field_validator("password_nuevo")
    @classmethod
    def validar_fortaleza(cls, valor: str) -> str:
        """Valida que la nueva contraseña tenga al menos una letra y un número."""
        if not any(c.isdigit() for c in valor):
            raise ValueError("La contraseña debe contener al menos un número")
        if not any(c.isalpha() for c in valor):
            raise ValueError("La contraseña debe contener al menos una letra")
        return valor


class SolicitarRecuperacionRequest(BaseModel):
    """Datos de entrada para solicitar la recuperación de contraseña."""

    correo: EmailStr


class RestablecerPasswordRequest(BaseModel):
    """Datos de entrada para restablecer la contraseña usando un token de recuperación."""

    token: str
    password_nuevo: str = Field(min_length=8)

    @field_validator("password_nuevo")
    @classmethod
    def validar_fortaleza(cls, valor: str) -> str:
        """Valida que la nueva contraseña tenga al menos una letra y un número."""
        if not any(c.isdigit() for c in valor):
            raise ValueError("La contraseña debe contener al menos un número")
        if not any(c.isalpha() for c in valor):
            raise ValueError("La contraseña debe contener al menos una letra")
        return valor


class RegistroClienteRequest(BaseModel):
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    documento: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validar_password_registro(cls, valor: str) -> str:
        if not any(c.isdigit() for c in valor) or not any(c.isalpha() for c in valor):
            raise ValueError("La contraseña debe contener letras y números")
        return valor

class PerfilClienteActualizarRequest(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    fecha_nacimiento: date | None = None
    preferencias: str | None = Field(default=None, max_length=2000)
    alergias: str | None = Field(default=None, max_length=2000)
