"""Implementación SQLAlchemy del repositorio de citas."""
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.models.appointment_model import Cita, CitaServicio
from app.models.client_model import Cliente
from app.models.employee_model import Empleado
from app.repositories.interfaces.cita_repository_interface import ICitaRepository
from app.utils.pagination import paginar_query

class CitaRepository(ICitaRepository):
    def __init__(self, db: Session): self.db = db

    def _options(self, query):
        return query.options(
            joinedload(Cita.cliente), joinedload(Cita.empleado),
            joinedload(Cita.servicios).joinedload(CitaServicio.servicio)
        )

    def obtener_por_id(self, cita_id):
        return self._options(self.db.query(Cita)).filter(Cita.id == cita_id).first()

    def listar(self, fecha_desde=None, fecha_hasta=None, empleado_id=None, cliente_id=None,
               estado=None, busqueda=None, pagina=1, tamano_pagina=20,
               orden_por="fecha", orden_direccion="asc"):
        query = self._options(self.db.query(Cita)).join(Cliente).join(Empleado)
        if fecha_desde: query = query.filter(Cita.fecha >= fecha_desde)
        if fecha_hasta: query = query.filter(Cita.fecha <= fecha_hasta)
        if empleado_id: query = query.filter(Cita.empleado_id == empleado_id)
        if cliente_id: query = query.filter(Cita.cliente_id == cliente_id)
        if estado: query = query.filter(Cita.estado == estado)
        if busqueda:
            term = f"%{busqueda.strip()}%"
            query = query.filter(or_(Cliente.nombres.ilike(term), Cliente.apellidos.ilike(term),
                                     Empleado.nombres.ilike(term), Empleado.apellidos.ilike(term)))
        return paginar_query(query, pagina, tamano_pagina, orden_por, orden_direccion, Cita)

    def guardar(self, cita):
        self.db.add(cita); self.db.flush(); return cita
