"""Pruebas básicas de validación del módulo de clientes."""
from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from app.schemas.client_schema import ClienteCrearRequest, ClienteCambiarEstadoRequest


def test_cliente_crear_normaliza_nombres():
    data = ClienteCrearRequest(nombres="  Ana   María ", apellidos=" Pérez ", correo="ANA@MAIL.COM")
    assert data.nombres == "Ana María"
    assert data.apellidos == "Pérez"


def test_fecha_nacimiento_futura_no_permitida():
    with pytest.raises(ValidationError):
        ClienteCrearRequest(nombres="Ana", apellidos="Pérez",
                            fecha_nacimiento=date.today() + timedelta(days=1))


def test_estado_invalido_no_permitido():
    with pytest.raises(ValidationError):
        ClienteCambiarEstadoRequest(estado="BORRADO")
