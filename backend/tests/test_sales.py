"""Pruebas unitarias de validaciones de la Fase 7."""
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.sale_schema import (CajaAbrirRequest, CajaMovimientoRequest, PagoCrear,
    VentaCrearRequest, VentaDetalleCrear)
from app.services.sale_service import money


def test_detalle_exige_un_solo_tipo():
    with pytest.raises(ValidationError):
        VentaDetalleCrear(producto_id=uuid.uuid4(), servicio_id=uuid.uuid4(), empleado_id=uuid.uuid4())


def test_servicio_exige_empleado():
    with pytest.raises(ValidationError):
        VentaDetalleCrear(servicio_id=uuid.uuid4())


def test_pago_digital_exige_referencia():
    with pytest.raises(ValidationError):
        PagoCrear(monto="20.00", metodo="YAPE")


def test_pago_efectivo_no_exige_referencia():
    pago=PagoCrear(monto="20.00", metodo="EFECTIVO")
    assert pago.monto == Decimal("20.00")


def test_venta_exige_detalles_y_pagos():
    with pytest.raises(ValidationError):
        VentaCrearRequest(detalles=[], pagos=[])


def test_movimiento_caja_valida_tipo():
    with pytest.raises(ValidationError):
        CajaMovimientoRequest(tipo="OTRO", concepto="Prueba", monto="10")


def test_monto_apertura_no_negativo():
    with pytest.raises(ValidationError):
        CajaAbrirRequest(monto_apertura="-1")


def test_redondeo_monetario():
    assert money("10.125") == Decimal("10.13")
