"""Implementación SQLAlchemy del repositorio de categorías y servicios."""
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.service_model import CategoriaServicio, Servicio
from app.repositories.interfaces.servicio_repository_interface import (
    ICategoriaServicioRepository,
    IServicioRepository,
)
from app.utils.pagination import paginar_query


class CategoriaServicioRepository(ICategoriaServicioRepository):
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, categoria_id: uuid.UUID) -> CategoriaServicio | None:
        return self.db.query(CategoriaServicio).options(joinedload(CategoriaServicio.servicios)).filter(
            CategoriaServicio.id == categoria_id
        ).first()

    def obtener_por_nombre(self, nombre: str) -> CategoriaServicio | None:
        return self.db.query(CategoriaServicio).filter(
            CategoriaServicio.nombre.ilike(nombre.strip())
        ).first()

    def listar(self, estado: str | None, busqueda: str | None, pagina: int,
               tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[CategoriaServicio], int]:
        query = self.db.query(CategoriaServicio).options(joinedload(CategoriaServicio.servicios))
        if estado:
            query = query.filter(CategoriaServicio.estado == estado)
        if busqueda:
            texto = f"%{busqueda.strip()}%"
            query = query.filter(or_(CategoriaServicio.nombre.ilike(texto),
                                     CategoriaServicio.descripcion.ilike(texto)))
        return paginar_query(query, pagina, tamano_pagina, orden_por,
                             orden_direccion, CategoriaServicio)

    def guardar(self, categoria: CategoriaServicio) -> CategoriaServicio:
        self.db.add(categoria)
        self.db.flush()
        self.db.refresh(categoria)
        return categoria


class ServicioRepository(IServicioRepository):
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, servicio_id: uuid.UUID) -> Servicio | None:
        return self.db.query(Servicio).options(joinedload(Servicio.categoria)).filter(
            Servicio.id == servicio_id
        ).first()

    def obtener_por_nombre_y_categoria(self, nombre: str,
                                        categoria_id: uuid.UUID) -> Servicio | None:
        return self.db.query(Servicio).filter(
            Servicio.nombre.ilike(nombre.strip()),
            Servicio.categoria_id == categoria_id,
        ).first()

    def listar(self, categoria_id: uuid.UUID | None, estado: str | None,
               busqueda: str | None, precio_min: float | None, precio_max: float | None,
               pagina: int, tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[Servicio], int]:
        query = self.db.query(Servicio).options(joinedload(Servicio.categoria))
        if categoria_id:
            query = query.filter(Servicio.categoria_id == categoria_id)
        if estado:
            query = query.filter(Servicio.estado == estado)
        if busqueda:
            texto = f"%{busqueda.strip()}%"
            query = query.join(CategoriaServicio).filter(or_(
                Servicio.nombre.ilike(texto),
                Servicio.descripcion.ilike(texto),
                CategoriaServicio.nombre.ilike(texto),
            ))
        if precio_min is not None:
            query = query.filter(Servicio.precio >= precio_min)
        if precio_max is not None:
            query = query.filter(Servicio.precio <= precio_max)
        return paginar_query(query, pagina, tamano_pagina, orden_por,
                             orden_direccion, Servicio)

    def guardar(self, servicio: Servicio) -> Servicio:
        self.db.add(servicio)
        self.db.flush()
        self.db.refresh(servicio)
        return servicio
