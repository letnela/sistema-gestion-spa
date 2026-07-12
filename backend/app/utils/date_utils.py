"""Utilidades de manejo de fechas y horas usadas en varios módulos del sistema."""
from datetime import date, datetime, time, timedelta


def combinar_fecha_hora(fecha: date, hora: time) -> datetime:
    """Combina un objeto date y un objeto time en un único datetime."""
    return datetime.combine(fecha, hora)


def rangos_se_superponen(inicio_1: time, fin_1: time, inicio_2: time, fin_2: time) -> bool:
    """Determina si dos rangos horarios del mismo día se superponen."""
    return inicio_1 < fin_2 and inicio_2 < fin_1


def sumar_minutos(hora: time, minutos: int) -> time:
    """Suma una cantidad de minutos a un objeto time, sin cruzar la medianoche."""
    base = datetime(2000, 1, 1, hora.hour, hora.minute, hora.second)
    resultado = base + timedelta(minutes=minutos)
    return resultado.time()


def inicio_y_fin_de_semana(fecha_referencia: date) -> tuple[date, date]:
    """Retorna el lunes y el domingo de la semana que contiene la fecha dada."""
    lunes = fecha_referencia - timedelta(days=fecha_referencia.weekday())
    domingo = lunes + timedelta(days=6)
    return lunes, domingo


def inicio_y_fin_de_mes(fecha_referencia: date) -> tuple[date, date]:
    """Retorna el primer y último día del mes que contiene la fecha dada."""
    primer_dia = fecha_referencia.replace(day=1)
    if fecha_referencia.month == 12:
        siguiente_mes = fecha_referencia.replace(year=fecha_referencia.year + 1, month=1, day=1)
    else:
        siguiente_mes = fecha_referencia.replace(month=fecha_referencia.month + 1, day=1)
    ultimo_dia = siguiente_mes - timedelta(days=1)
    return primer_dia, ultimo_dia
