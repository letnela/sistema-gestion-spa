"""Esquemas de respuesta para Dashboard y Reportes (Fase 9)."""
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class RangoFechas(BaseModel):
    fecha_desde: date
    fecha_hasta: date

    @model_validator(mode="after")
    def validar_rango(self):
        if self.fecha_hasta < self.fecha_desde:
            raise ValueError("fecha_hasta no puede ser anterior a fecha_desde")
        if (self.fecha_hasta - self.fecha_desde).days > 366:
            raise ValueError("El rango máximo permitido es de 366 días")
        return self


class IndicadoresDashboard(BaseModel):
    ventas_hoy: Decimal = Decimal("0.00")
    ventas_periodo: Decimal = Decimal("0.00")
    cantidad_ventas: int = 0
    ticket_promedio: Decimal = Decimal("0.00")
    citas_hoy: int = 0
    citas_periodo: int = 0
    citas_finalizadas: int = 0
    citas_canceladas: int = 0
    clientes_nuevos: int = 0
    productos_stock_bajo: int = 0
    valor_inventario: Decimal = Decimal("0.00")


class SerieTemporalItem(BaseModel):
    fecha: date
    total: Decimal = Decimal("0.00")
    cantidad: int = 0


class RankingItem(BaseModel):
    id: str | None = None
    nombre: str
    cantidad: int = 0
    total: Decimal = Decimal("0.00")


class EstadoCitaItem(BaseModel):
    estado: str
    cantidad: int
    porcentaje: Decimal = Decimal("0.00")


class DashboardResponse(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    indicadores: IndicadoresDashboard
    ventas_por_dia: list[SerieTemporalItem]
    citas_por_estado: list[EstadoCitaItem]
    servicios_mas_vendidos: list[RankingItem]
    productos_mas_vendidos: list[RankingItem]
    empleados_destacados: list[RankingItem]


class ReporteVentasResponse(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    total_bruto: Decimal
    descuentos: Decimal
    impuestos: Decimal
    total_neto: Decimal
    cantidad_ventas: int
    ticket_promedio: Decimal
    ventas_por_dia: list[SerieTemporalItem]
    metodos_pago: list[RankingItem]


class ReporteCitasResponse(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    total: int
    finalizadas: int
    canceladas: int
    no_asistio: int
    tasa_finalizacion: Decimal
    estados: list[EstadoCitaItem]
    servicios: list[RankingItem]
    empleados: list[RankingItem]


class ReporteInventarioResponse(BaseModel):
    cantidad_productos: int
    agotados: int
    stock_bajo: int
    unidades_totales: int
    valor_costo: Decimal
    valor_venta: Decimal
    productos_criticos: list[RankingItem]
