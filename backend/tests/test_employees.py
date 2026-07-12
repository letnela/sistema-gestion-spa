"""Pruebas unitarias de validaciones de la Fase 5."""
from datetime import date, time, timedelta
import pytest
from pydantic import ValidationError
from app.schemas.employee_schema import EmpleadoCrearRequest, HorarioEmpleadoRequest, VacacionEmpleadoCrearRequest

def test_empleado_rechaza_fecha_futura():
    with pytest.raises(ValidationError):
        EmpleadoCrearRequest(nombres="Ana", apellidos="Pérez", documento="12345678", cargo="ESTILISTA", fecha_ingreso=date.today()+timedelta(days=1))

def test_comision_fuera_de_rango():
    with pytest.raises(ValidationError):
        EmpleadoCrearRequest(nombres="Ana", apellidos="Pérez", documento="12345678", cargo="ESTILISTA", fecha_ingreso=date.today(), porcentaje_comision_default=101)

def test_horario_valido():
    h=HorarioEmpleadoRequest(dia_semana=1,hora_entrada=time(9),hora_salida=time(18),hora_inicio_descanso=time(13),hora_fin_descanso=time(14))
    assert h.dia_semana == 1

def test_horario_invalido():
    with pytest.raises(ValidationError):
        HorarioEmpleadoRequest(dia_semana=1,hora_entrada=time(18),hora_salida=time(9))

def test_vacaciones_fechas_invalidas():
    with pytest.raises(ValidationError):
        VacacionEmpleadoCrearRequest(fecha_inicio=date(2026,8,10),fecha_fin=date(2026,8,1))
