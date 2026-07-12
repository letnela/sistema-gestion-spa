"""Esquemas de validación y respuesta del módulo de empleados."""
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.constants import EstadoGenerico


class EmpleadoBase(BaseModel):
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    documento: str | None = Field(default=None, min_length=6, max_length=30)
    telefono: str | None = Field(default=None, min_length=6, max_length=30)
    correo: EmailStr | None = None
    cargo: str = Field(default="ESTILISTA", min_length=2, max_length=100)
    especialidad: str | None = Field(default=None, max_length=150)
    salario: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    porcentaje_comision_default: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    fecha_ingreso: date
    usuario_id: uuid.UUID | None = None

    @field_validator("nombres", "apellidos", "cargo", "especialidad", mode="before")
    @classmethod
    def limpiar_texto(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("documento", "telefono", mode="before")
    @classmethod
    def limpiar_identificadores(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    @field_validator("correo", mode="before")
    @classmethod
    def normalizar_correo(cls, value):
        return value.lower().strip() if isinstance(value, str) and value.strip() else None

    @field_validator("fecha_ingreso")
    @classmethod
    def fecha_no_futura(cls, value: date):
        if value > date.today():
            raise ValueError("La fecha de ingreso no puede estar en el futuro")
        return value


class EmpleadoCrearRequest(EmpleadoBase):
    servicio_ids: list[uuid.UUID] = Field(default_factory=list)


class EmpleadoActualizarRequest(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    documento: str | None = Field(default=None, min_length=6, max_length=30)
    telefono: str | None = Field(default=None, min_length=6, max_length=30)
    correo: EmailStr | None = None
    cargo: str | None = Field(default=None, min_length=2, max_length=100)
    especialidad: str | None = Field(default=None, max_length=150)
    salario: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    porcentaje_comision_default: Decimal | None = Field(default=None, ge=0, le=100)
    fecha_ingreso: date | None = None
    usuario_id: uuid.UUID | None = None
    servicio_ids: list[uuid.UUID] | None = None


class EmpleadoCambiarEstadoRequest(BaseModel):
    estado: str = Field(pattern="^(ACTIVO|INACTIVO)$")


class ServicioEmpleadoResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    precio: Decimal
    duracion_minutos: int


class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    usuario_id: uuid.UUID | None
    nombres: str
    apellidos: str
    nombre_completo: str
    documento: str | None
    telefono: str | None
    correo: str | None
    cargo: str
    especialidad: str | None
    salario: Decimal | None
    porcentaje_comision_default: Decimal
    fecha_ingreso: date
    estado: str
    servicios: list[ServicioEmpleadoResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class HorarioEmpleadoRequest(BaseModel):
    dia_semana: int = Field(ge=1, le=7)
    hora_entrada: time
    hora_salida: time
    hora_inicio_descanso: time | None = None
    hora_fin_descanso: time | None = None
    es_dia_libre: bool = False

    @model_validator(mode="after")
    def validar_horas(self):
        if not self.es_dia_libre and self.hora_salida <= self.hora_entrada:
            raise ValueError("La hora de salida debe ser posterior a la hora de entrada")
        if (self.hora_inicio_descanso is None) != (self.hora_fin_descanso is None):
            raise ValueError("Debe indicar el inicio y fin del descanso")
        if self.hora_inicio_descanso and not (self.hora_entrada < self.hora_inicio_descanso < self.hora_fin_descanso < self.hora_salida):
            raise ValueError("El descanso debe estar dentro del horario laboral")
        return self


class HorarioEmpleadoResponse(HorarioEmpleadoRequest):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empleado_id: uuid.UUID


class VacacionEmpleadoCrearRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    motivo: str | None = Field(default=None, max_length=255)
    aprobado: bool = True

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha final no puede ser anterior a la fecha inicial")
        return self


class VacacionEmpleadoResponse(VacacionEmpleadoCrearRequest):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empleado_id: uuid.UUID


class BloqueoHorarioCrearRequest(BaseModel):
    fecha: date
    hora_inicio: time
    hora_fin: time
    motivo: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validar_horas(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora final debe ser posterior a la hora inicial")
        return self


class BloqueoHorarioResponse(BloqueoHorarioCrearRequest):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empleado_id: uuid.UUID
