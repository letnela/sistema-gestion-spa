import uuid
from datetime import date,time
from pydantic import BaseModel, Field
class PortalCitaCrearRequest(BaseModel):
    empleado_id: uuid.UUID
    fecha: date
    hora_inicio: time
    servicio_ids: list[uuid.UUID] = Field(min_length=1)
    notas: str | None = Field(default=None,max_length=1000)
class PortalCitaReprogramarRequest(BaseModel):
    empleado_id: uuid.UUID | None = None
    fecha: date | None = None
    hora_inicio: time | None = None
    servicio_ids: list[uuid.UUID] | None = None
    notas: str | None = Field(default=None,max_length=1000)
class PortalCancelarRequest(BaseModel):
    motivo: str = Field(min_length=3,max_length=255)
