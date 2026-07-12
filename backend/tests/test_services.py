"""Pruebas unitarias básicas de validación para la Fase 4."""
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.service_schema import (
    CambiarEstadoRequest,
    CategoriaServicioCrearRequest,
    ServicioCrearRequest,
)


def test_categoria_limpia_espacios():
    datos = CategoriaServicioCrearRequest(nombre="  Cuidado   capilar  ")
    assert datos.nombre == "Cuidado capilar"


def test_servicio_valido():
    datos = ServicioCrearRequest(
        categoria_id=uuid4(),
        nombre="Corte clásico",
        precio=Decimal("35.50"),
        duracion_minutos=45,
        porcentaje_comision=Decimal("15.00"),
    )
    assert datos.precio == Decimal("35.50")
    assert datos.duracion_minutos == 45


def test_servicio_rechaza_precio_cero():
    with pytest.raises(ValidationError):
        ServicioCrearRequest(
            categoria_id=uuid4(), nombre="Corte", precio=0, duracion_minutos=30
        )


def test_servicio_rechaza_comision_mayor_cien():
    with pytest.raises(ValidationError):
        ServicioCrearRequest(
            categoria_id=uuid4(), nombre="Corte", precio=20,
            duracion_minutos=30, porcentaje_comision=101
        )


def test_estado_invalido():
    with pytest.raises(ValidationError):
        CambiarEstadoRequest(estado="ELIMINADO")
