"""Esquemas de ventas, pagos y caja."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from app.core.constants import MetodoPago


class VentaDetalleCrear(BaseModel):
    producto_id: uuid.UUID | None = None
    servicio_id: uuid.UUID | None = None
    empleado_id: uuid.UUID | None = None
    cantidad: int = Field(default=1, ge=1, le=999)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)

    @model_validator(mode="after")
    def validar_item(self):
        if (self.producto_id is None) == (self.servicio_id is None):
            raise ValueError("Cada detalle debe contener exactamente un producto o un servicio")
        if self.servicio_id and not self.empleado_id:
            raise ValueError("Los servicios vendidos requieren un empleado")
        return self


class PagoCrear(BaseModel):
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    metodo: Literal[tuple(MetodoPago.TODOS)]
    referencia: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def validar_referencia(self):
        if self.metodo in {MetodoPago.TARJETA, MetodoPago.TRANSFERENCIA, MetodoPago.YAPE, MetodoPago.PLIN} and not self.referencia:
            raise ValueError("La referencia es obligatoria para el método de pago seleccionado")
        return self


class VentaCrearRequest(BaseModel):
    cita_id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    detalles: list[VentaDetalleCrear] = Field(min_length=1)
    pagos: list[PagoCrear] = Field(min_length=1)
    descuento_global: Decimal = Field(default=Decimal("0.00"), ge=0)
    porcentaje_impuesto: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class PagoResponse(BaseModel):
    id: uuid.UUID
    monto: Decimal
    metodo: str
    referencia: str | None
    estado: str
    fecha: datetime
    model_config = {"from_attributes": True}


class VentaDetalleResponse(BaseModel):
    id: uuid.UUID
    producto_id: uuid.UUID | None
    servicio_id: uuid.UUID | None
    empleado_id: uuid.UUID | None
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal


class VentaResponse(BaseModel):
    id: uuid.UUID
    numero_comprobante: str
    cliente_id: uuid.UUID | None
    cita_id: uuid.UUID | None = None
    cliente_nombre: str | None
    usuario_id: uuid.UUID
    subtotal: Decimal
    descuento: Decimal
    impuesto: Decimal
    total: Decimal
    estado: str
    motivo_anulacion: str | None
    fecha: datetime
    detalles: list[VentaDetalleResponse]
    pagos: list[PagoResponse]


class AnularVentaRequest(BaseModel):
    motivo: str = Field(min_length=5, max_length=255)


class CajaAbrirRequest(BaseModel):
    monto_apertura: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    observaciones: str | None = Field(default=None, max_length=500)


class CajaMovimientoRequest(BaseModel):
    tipo: Literal["INGRESO", "EGRESO"]
    concepto: str = Field(min_length=3, max_length=200)
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    referencia: str | None = Field(default=None, max_length=150)


class CajaCerrarRequest(BaseModel):
    monto_cierre_declarado: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    observaciones: str | None = Field(default=None, max_length=500)


class CajaMovimientoResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    concepto: str
    monto: Decimal
    referencia: str | None
    fecha: datetime
    model_config = {"from_attributes": True}


class CajaSesionResponse(BaseModel):
    id: uuid.UUID
    usuario_apertura_id: uuid.UUID
    usuario_cierre_id: uuid.UUID | None
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    monto_apertura: Decimal
    monto_esperado: Decimal | None = None
    monto_cierre_declarado: Decimal | None
    monto_cierre_calculado: Decimal | None
    diferencia: Decimal | None
    estado: str
    observaciones: str | None
    movimientos: list[CajaMovimientoResponse] = []
    model_config = {"from_attributes": True}
