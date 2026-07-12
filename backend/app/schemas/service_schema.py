"""Esquemas Pydantic para categorías y servicios del salón."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.core.constants import EstadoGenerico


class CategoriaServicioCrearRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor

    @field_validator("descripcion")
    @classmethod
    def limpiar_descripcion(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor is not None else None


class CategoriaServicioActualizarRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class CambiarEstadoRequest(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor: str) -> str:
        valor = valor.upper().strip()
        if valor not in EstadoGenerico.TODOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {EstadoGenerico.TODOS}")
        return valor


class CategoriaServicioResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: str | None = None
    estado: str
    cantidad_servicios: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServicioCrearRequest(BaseModel):
    categoria_id: uuid.UUID
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = None
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    duracion_minutos: int = Field(ge=5, le=1440)
    imagen_url: HttpUrl | None = None
    porcentaje_comision: Decimal = Field(default=Decimal("10.00"), ge=0, le=100,
                                          max_digits=5, decimal_places=2)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str) -> str:
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor

    @field_validator("descripcion")
    @classmethod
    def limpiar_descripcion(cls, valor: str | None) -> str | None:
        return valor.strip() or None if valor is not None else None


class ServicioActualizarRequest(BaseModel):
    categoria_id: uuid.UUID | None = None
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    duracion_minutos: int | None = Field(default=None, ge=5, le=1440)
    imagen_url: HttpUrl | None = None
    porcentaje_comision: Decimal | None = Field(default=None, ge=0, le=100,
                                                 max_digits=5, decimal_places=2)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        valor = " ".join(valor.strip().split())
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor


class ServicioResponse(BaseModel):
    id: uuid.UUID
    categoria_id: uuid.UUID
    categoria_nombre: str
    nombre: str
    descripcion: str | None = None
    precio: Decimal
    duracion_minutos: int
    imagen_url: str | None = None
    porcentaje_comision: Decimal
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
