"""Implementación SQLAlchemy del repositorio de empleados."""
import uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.models.employee_model import Empleado, EmpleadoServicio
from app.repositories.interfaces.empleado_repository_interface import IEmpleadoRepository
from app.utils.pagination import paginar_query

class EmpleadoRepository(IEmpleadoRepository):
    def __init__(self, db: Session): self.db = db

    def _base(self):
        return self.db.query(Empleado).options(
            joinedload(Empleado.servicios).joinedload(EmpleadoServicio.servicio)
        )

    def obtener_por_id(self, empleado_id: uuid.UUID):
        return self.db.query(Empleado).options(
            joinedload(Empleado.servicios).joinedload(EmpleadoServicio.servicio),
            joinedload(Empleado.horarios), joinedload(Empleado.vacaciones),
            joinedload(Empleado.bloqueos)
        ).filter(Empleado.id == empleado_id).first()

    def obtener_por_documento(self, documento: str):
        return self.db.query(Empleado).filter(Empleado.documento == documento.strip()).first()

    def obtener_por_correo(self, correo: str):
        return self.db.query(Empleado).filter(Empleado.correo == correo.lower().strip()).first()

    def obtener_por_usuario(self, usuario_id: uuid.UUID):
        return self.db.query(Empleado).filter(Empleado.usuario_id == usuario_id).first()

    def listar(self, estado=None, cargo=None, busqueda=None, pagina=1, tamano_pagina=20,
               orden_por="created_at", orden_direccion="desc"):
        query = self.db.query(Empleado).options(joinedload(Empleado.servicios).joinedload(EmpleadoServicio.servicio))
        if estado: query = query.filter(Empleado.estado == estado)
        if cargo: query = query.filter(Empleado.cargo.ilike(cargo.strip()))
        if busqueda:
            t = f"%{busqueda.strip()}%"
            query = query.filter(or_(Empleado.nombres.ilike(t), Empleado.apellidos.ilike(t),
                                     Empleado.documento.ilike(t), Empleado.correo.ilike(t),
                                     Empleado.cargo.ilike(t), Empleado.especialidad.ilike(t)))
        return paginar_query(query, pagina, tamano_pagina, orden_por, orden_direccion, Empleado)

    def guardar(self, empleado):
        self.db.add(empleado); self.db.flush(); return empleado
