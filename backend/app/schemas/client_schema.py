"""Esquemas Pydantic para la gestión de clientes."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import EstadoGenerico


class ClienteCrearRequest(BaseModel):
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    documento: str | None = Field(default=None, max_length=30)
    telefono: str | None = Field(default=None, max_length=30)
    correo: EmailStr | None = None
    direccion: str | None = Field(default=None, max_length=255)
    fecha_nacimiento: date | None = None
    observaciones: str | None = None
    preferencias: str | None = None
    alergias: str | None = None
    crear_acceso_portal: bool = False
    password_portal: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El campo no puede estar vacío")
        return valor

    @field_validator("documento", "telefono", "direccion", "observaciones", "preferencias", "alergias")
    @classmethod
    def limpiar_opcional(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor is not None else None

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date | None) -> date | None:
        if valor and valor > date.today():
            raise ValueError("La fecha de nacimiento no puede estar en el futuro")
        return valor


class ClienteActualizarRequest(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    documento: str | None = Field(default=None, max_length=30)
    telefono: str | None = Field(default=None, max_length=30)
    correo: EmailStr | None = None
    direccion: str | None = Field(default=None, max_length=255)
    fecha_nacimiento: date | None = None
    observaciones: str | None = None
    preferencias: str | None = None
    alergias: str | None = None

    @field_validator("nombres", "apellidos")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El campo no puede estar vacío")
        return valor

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date | None) -> date | None:
        if valor and valor > date.today():
            raise ValueError("La fecha de nacimiento no puede estar en el futuro")
        return valor


class ClienteCambiarEstadoRequest(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor: str) -> str:
        valor = valor.upper().strip()
        if valor not in EstadoGenerico.TODOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {EstadoGenerico.TODOS}")
        return valor


class ClienteResponse(BaseModel):
    id: uuid.UUID
    nombres: str
    apellidos: str
    nombre_completo: str
    documento: str | None = None
    telefono: str | None = None
    correo: EmailStr | None = None
    direccion: str | None = None
    fecha_nacimiento: date | None = None
    observaciones: str | None = None
    preferencias: str | None = None
    alergias: str | None = None
    estado: str
    created_at: datetime
    updated_at: datetime
    usuario_id: uuid.UUID | None = None
    portal_estado: str | None = None
    portal_ultimo_login: datetime | None = None
    portal_debe_cambiar_password: bool | None = None

    model_config = {"from_attributes": True}


class ClientePortalCrearRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str | None) -> str | None:
        if valor and (not any(c.isalpha() for c in valor) or not any(c.isdigit() for c in valor)):
            raise ValueError("La contraseña debe contener letras y números")
        return valor


class ClientePortalEstadoRequest(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def validar_estado_portal(cls, valor: str) -> str:
        valor = valor.upper().strip()
        if valor not in EstadoGenerico.TODOS:
            raise ValueError("Estado de portal inválido")
        return valor


class ClientePortalAccesoResponse(BaseModel):
    usuario_id: uuid.UUID
    correo: EmailStr
    estado: str
    password_temporal: str | None = None
    debe_cambiar_password: bool
