from datetime import date, timedelta
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.report_schema import RangoFechas, IndicadoresDashboard, SerieTemporalItem, DashboardResponse


def test_rango_valido():
    r=RangoFechas(fecha_desde=date(2026,1,1),fecha_hasta=date(2026,1,31))
    assert r.fecha_desde < r.fecha_hasta


def test_rango_invertido_no_permitido():
    with pytest.raises(ValidationError):
        RangoFechas(fecha_desde=date(2026,2,1),fecha_hasta=date(2026,1,1))


def test_rango_mayor_a_un_ano_no_permitido():
    with pytest.raises(ValidationError):
        RangoFechas(fecha_desde=date(2025,1,1),fecha_hasta=date(2026,2,1))


def test_indicadores_decimal():
    x=IndicadoresDashboard(ventas_periodo=Decimal('125.50'),cantidad_ventas=2,ticket_promedio=Decimal('62.75'))
    assert x.ticket_promedio == Decimal('62.75')


def test_dashboard_acepta_series_vacias():
    d=DashboardResponse(fecha_desde=date.today(),fecha_hasta=date.today(),indicadores=IndicadoresDashboard(),ventas_por_dia=[],citas_por_estado=[],servicios_mas_vendidos=[],productos_mas_vendidos=[],empleados_destacados=[])
    assert d.indicadores.cantidad_ventas == 0
