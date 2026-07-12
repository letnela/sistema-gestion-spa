from datetime import date, time
import uuid
import pytest
from pydantic import ValidationError
from app.schemas.appointment_schema import CitaCrearRequest, CitaCambiarEstadoRequest
from app.services.appointment_service import AppointmentService, TRANSICIONES
from app.core.constants import EstadoCita

def test_cita_requiere_servicio():
    with pytest.raises(ValidationError):
        CitaCrearRequest(cliente_id=uuid.uuid4(),empleado_id=uuid.uuid4(),fecha=date.today(),hora_inicio=time(9),servicio_ids=[])

def test_no_acepta_servicios_duplicados():
    sid=uuid.uuid4()
    with pytest.raises(ValidationError):
        CitaCrearRequest(cliente_id=uuid.uuid4(),empleado_id=uuid.uuid4(),fecha=date.today(),hora_inicio=time(9),servicio_ids=[sid,sid])

def test_cancelacion_requiere_motivo():
    with pytest.raises(ValidationError): CitaCambiarEstadoRequest(estado=EstadoCita.CANCELADA)

def test_suma_minutos():
    assert AppointmentService._sumar_minutos(time(9,30),90)==time(11,0)

def test_transiciones_finalizada_son_terminales():
    assert TRANSICIONES[EstadoCita.FINALIZADA] == set()
