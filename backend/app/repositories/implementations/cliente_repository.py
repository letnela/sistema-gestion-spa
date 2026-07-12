"""Implementación SQLAlchemy del repositorio de clientes."""
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.client_model import Cliente
from app.repositories.interfaces.cliente_repository_interface import IClienteRepository
from app.utils.pagination import paginar_query


class ClienteRepository(IClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, cliente_id: uuid.UUID) -> Cliente | None:
        return self.db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.eliminado.is_(False)).first()

    def obtener_por_documento(self, documento: str) -> Cliente | None:
        return self.db.query(Cliente).filter(
            Cliente.documento == documento.strip(), Cliente.eliminado.is_(False)
        ).first()

    def obtener_por_correo(self, correo: str) -> Cliente | None:
        return self.db.query(Cliente).filter(
            Cliente.correo == correo.lower().strip(), Cliente.eliminado.is_(False)
        ).first()

    def listar(self, estado: str | None = None, busqueda: str | None = None,
               pagina: int = 1, tamano_pagina: int = 20,
               orden_por: str | None = "created_at", orden_direccion: str = "desc") -> tuple[list[Cliente], int]:
        query = self.db.query(Cliente).filter(Cliente.eliminado.is_(False))
        if estado:
            query = query.filter(Cliente.estado == estado)
        if busqueda:
            texto = f"%{busqueda.strip()}%"
            query = query.filter(or_(
                Cliente.nombres.ilike(texto), Cliente.apellidos.ilike(texto),
                Cliente.documento.ilike(texto), Cliente.telefono.ilike(texto),
                Cliente.correo.ilike(texto),
            ))
        return paginar_query(query, pagina, tamano_pagina, orden_por, orden_direccion, Cliente)

    def crear(self, cliente: Cliente) -> Cliente:
        self.db.add(cliente)
        self.db.flush()
        self.db.refresh(cliente)
        return cliente

    def actualizar(self, cliente: Cliente) -> Cliente:
        self.db.flush()
        self.db.refresh(cliente)
        return cliente
