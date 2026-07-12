"""Esquemas del módulo de agenda y citas."""
import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.constants import EstadoCita

class CitaCrearRequest(BaseModel):
    cliente_id: uuid.UUID
    empleado_id: uuid.UUID
    fecha: date
    hora_inicio: time
    servicio_ids: list[uuid.UUID] = Field(min_length=1)
    notas: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("servicio_ids")
    @classmethod
    def servicios_sin_duplicados(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("No se permiten servicios duplicados")
        return value

class CitaActualizarRequest(BaseModel):
    cliente_id: Optional[uuid.UUID] = None
    empleado_id: Optional[uuid.UUID] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    servicio_ids: Optional[list[uuid.UUID]] = None
    notas: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("servicio_ids")
    @classmethod
    def validar_servicios(cls, value):
        if value is not None and not value:
            raise ValueError("Debe seleccionar al menos un servicio")
        if value is not None and len(value) != len(set(value)):
            raise ValueError("No se permiten servicios duplicados")
        return value

class CitaCambiarEstadoRequest(BaseModel):
    estado: str
    motivo_cancelacion: Optional[str] = Field(default=None, max_length=255)

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, value):
        if value not in EstadoCita.TODOS:
            raise ValueError(f"Estado inválido. Valores permitidos: {', '.join(EstadoCita.TODOS)}")
        return value

    @model_validator(mode="after")
    def motivo_requerido(self):
        if self.estado == EstadoCita.CANCELADA and not self.motivo_cancelacion:
            raise ValueError("Debe indicar el motivo de cancelación")
        return self

class CitaServicioResponse(BaseModel):
    id: uuid.UUID
    servicio_id: uuid.UUID
    nombre: str
    precio_aplicado: Decimal
    duracion_aplicada_minutos: int
    model_config = {"from_attributes": True}

class CitaResponse(BaseModel):
    id: uuid.UUID
    cliente_id: uuid.UUID
    cliente_nombre: str
    empleado_id: uuid.UUID
    empleado_nombre: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    duracion_total_minutos: int
    precio_total: Decimal
    estado: str
    notas: Optional[str]
    motivo_cancelacion: Optional[str]
    servicios: list[CitaServicioResponse]
    created_at: datetime
    updated_at: datetime

class DisponibilidadResponse(BaseModel):
    disponible: bool
    empleado_id: uuid.UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    motivo: Optional[str] = None

class ResumenAgendaResponse(BaseModel):
    fecha: date
    total_citas: int
    pendientes: int
    confirmadas: int
    en_proceso: int
    finalizadas: int
    canceladas: int
    no_asistio: int


class HorarioDisponibleResponse(BaseModel):
    hora_inicio: time
    hora_fin: time
    disponible: bool = True

