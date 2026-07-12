"""Endpoints del Dashboard y Reportes (Fase 9)."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito
from app.schemas.report_schema import DashboardResponse, ReporteCitasResponse, ReporteInventarioResponse, ReporteVentasResponse, RangoFechas
from app.services.report_service import ReportService

router=APIRouter(prefix="/reports",tags=["Dashboard y Reportes"],dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))])

def rango(fecha_desde:date|None,fecha_hasta:date|None):
    hasta=fecha_hasta or date.today(); desde=fecha_desde or (hasta-timedelta(days=29)); return RangoFechas(fecha_desde=desde,fecha_hasta=hasta)

@router.get("/dashboard",response_model=RespuestaExito[DashboardResponse])
def dashboard(fecha_desde:date|None=None,fecha_hasta:date|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    r=rango(fecha_desde,fecha_hasta); return RespuestaExito(data=ReportService(db).dashboard(r.fecha_desde,r.fecha_hasta))

@router.get("/sales",response_model=RespuestaExito[ReporteVentasResponse])
def ventas(fecha_desde:date|None=None,fecha_hasta:date|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    r=rango(fecha_desde,fecha_hasta); return RespuestaExito(data=ReportService(db).reporte_ventas(r.fecha_desde,r.fecha_hasta))

@router.get("/appointments",response_model=RespuestaExito[ReporteCitasResponse])
def citas(fecha_desde:date|None=None,fecha_hasta:date|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    r=rango(fecha_desde,fecha_hasta); return RespuestaExito(data=ReportService(db).reporte_citas(r.fecha_desde,r.fecha_hasta))

@router.get("/inventory",response_model=RespuestaExito[ReporteInventarioResponse])
def inventario(db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=ReportService(db).reporte_inventario())

@router.get("/sales/export.xlsx")
def exportar_excel(fecha_desde:date|None=None,fecha_hasta:date|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    r=rango(fecha_desde,fecha_hasta); data=ReportService(db).exportar_ventas_xlsx(r.fecha_desde,r.fecha_hasta)
    return Response(data,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="ventas_{r.fecha_desde}_{r.fecha_hasta}.xlsx"'})

@router.get("/executive/export.pdf")
def exportar_pdf(fecha_desde:date|None=None,fecha_hasta:date|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    r=rango(fecha_desde,fecha_hasta); data=ReportService(db).exportar_resumen_pdf(r.fecha_desde,r.fecha_hasta)
    return Response(data,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="reporte_ejecutivo_{r.fecha_desde}_{r.fecha_hasta}.pdf"'})
