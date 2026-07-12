"""Lógica de negocio para categorías y servicios del salón."""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import AccionAuditoria, EstadoGenerico
from app.core.exceptions import ConflictException, NotFoundException
from app.models.service_model import CategoriaServicio, Servicio
from app.models.user_model import Usuario
from app.repositories.implementations.servicio_repository import (
    CategoriaServicioRepository,
    ServicioRepository,
)
from app.schemas.service_schema import (
    CategoriaServicioActualizarRequest,
    CategoriaServicioCrearRequest,
    ServicioActualizarRequest,
    ServicioCrearRequest,
)
from app.services.audit_service import registrar_auditoria


class CategoriaServicioService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoriaServicioRepository(db)

    def listar(self, estado: str | None, busqueda: str | None, pagina: int,
               tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[CategoriaServicio], int]:
        return self.repo.listar(estado, busqueda, pagina, tamano_pagina,
                                orden_por, orden_direccion)

    def obtener(self, categoria_id: uuid.UUID) -> CategoriaServicio:
        categoria = self.repo.obtener_por_id(categoria_id)
        if not categoria:
            raise NotFoundException("La categoría de servicio no existe")
        return categoria

    def crear(self, datos: CategoriaServicioCrearRequest, actor: Usuario) -> CategoriaServicio:
        if self.repo.obtener_por_nombre(datos.nombre):
            raise ConflictException(f"Ya existe una categoría llamada {datos.nombre}")
        categoria = CategoriaServicio(**datos.model_dump(), estado=EstadoGenerico.ACTIVO)
        self.repo.guardar(categoria)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.CREAR, "SERVICIOS",
                            "CategoriaServicio", str(categoria.id),
                            valor_nuevo={"nombre": categoria.nombre})
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def actualizar(self, categoria_id: uuid.UUID, datos: CategoriaServicioActualizarRequest,
                   actor: Usuario) -> CategoriaServicio:
        categoria = self.obtener(categoria_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "nombre" in cambios:
            existente = self.repo.obtener_por_nombre(cambios["nombre"])
            if existente and existente.id != categoria.id:
                raise ConflictException(f"Ya existe una categoría llamada {cambios['nombre']}")
        anterior = {campo: getattr(categoria, campo) for campo in cambios}
        for campo, valor in cambios.items():
            setattr(categoria, campo, valor)
        self.repo.guardar(categoria)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "SERVICIOS",
                            "CategoriaServicio", str(categoria.id), anterior, cambios)
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def cambiar_estado(self, categoria_id: uuid.UUID, estado: str,
                       actor: Usuario) -> CategoriaServicio:
        categoria = self.obtener(categoria_id)
        anterior = categoria.estado
        categoria.estado = estado
        self.repo.guardar(categoria)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "SERVICIOS",
                            "CategoriaServicio", str(categoria.id),
                            {"estado": anterior}, {"estado": estado})
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def eliminar(self, categoria_id: uuid.UUID, actor: Usuario) -> None:
        categoria = self.obtener(categoria_id)
        if categoria.servicios:
            raise ConflictException("No se puede eliminar una categoría que contiene servicios")
        registrar_auditoria(self.db, actor.id, AccionAuditoria.ELIMINAR, "SERVICIOS",
                            "CategoriaServicio", str(categoria.id),
                            valor_anterior={"nombre": categoria.nombre})
        self.db.delete(categoria)
        self.db.commit()


class ServicioService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServicioRepository(db)
        self.categoria_repo = CategoriaServicioRepository(db)

    def listar(self, categoria_id: uuid.UUID | None, estado: str | None,
               busqueda: str | None, precio_min: float | None, precio_max: float | None,
               pagina: int, tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[Servicio], int]:
        if precio_min is not None and precio_max is not None and precio_min > precio_max:
            raise ConflictException("El precio mínimo no puede ser mayor al precio máximo")
        return self.repo.listar(categoria_id, estado, busqueda, precio_min, precio_max,
                                pagina, tamano_pagina, orden_por, orden_direccion)

    def obtener(self, servicio_id: uuid.UUID) -> Servicio:
        servicio = self.repo.obtener_por_id(servicio_id)
        if not servicio:
            raise NotFoundException("El servicio solicitado no existe")
        return servicio

    def _validar_categoria(self, categoria_id: uuid.UUID) -> CategoriaServicio:
        categoria = self.categoria_repo.obtener_por_id(categoria_id)
        if not categoria:
            raise NotFoundException("La categoría seleccionada no existe")
        if categoria.estado != EstadoGenerico.ACTIVO:
            raise ConflictException("La categoría seleccionada está inactiva")
        return categoria

    def _validar_nombre(self, nombre: str, categoria_id: uuid.UUID,
                        servicio_id: uuid.UUID | None = None) -> None:
        existente = self.repo.obtener_por_nombre_y_categoria(nombre, categoria_id)
        if existente and existente.id != servicio_id:
            raise ConflictException("Ya existe un servicio con ese nombre en la categoría")

    def crear(self, datos: ServicioCrearRequest, actor: Usuario) -> Servicio:
        self._validar_categoria(datos.categoria_id)
        self._validar_nombre(datos.nombre, datos.categoria_id)
        payload = datos.model_dump()
        if payload.get("imagen_url") is not None:
            payload["imagen_url"] = str(payload["imagen_url"])
        servicio = Servicio(**payload, estado=EstadoGenerico.ACTIVO)
        self.repo.guardar(servicio)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.CREAR, "SERVICIOS",
                            "Servicio", str(servicio.id), valor_nuevo={
                                "nombre": servicio.nombre,
                                "precio": str(servicio.precio),
                                "categoria_id": str(servicio.categoria_id),
                            })
        self.db.commit()
        return self.obtener(servicio.id)

    def actualizar(self, servicio_id: uuid.UUID, datos: ServicioActualizarRequest,
                   actor: Usuario) -> Servicio:
        servicio = self.obtener(servicio_id)
        cambios = datos.model_dump(exclude_unset=True)
        categoria_id = cambios.get("categoria_id", servicio.categoria_id)
        nombre = cambios.get("nombre", servicio.nombre)
        self._validar_categoria(categoria_id)
        self._validar_nombre(nombre, categoria_id, servicio.id)
        if cambios.get("imagen_url") is not None:
            cambios["imagen_url"] = str(cambios["imagen_url"])
        anterior = {campo: str(getattr(servicio, campo)) if campo in {"precio", "porcentaje_comision", "categoria_id"}
                    else getattr(servicio, campo) for campo in cambios}
        for campo, valor in cambios.items():
            setattr(servicio, campo, valor)
        self.repo.guardar(servicio)
        nuevos = {campo: str(valor) if campo in {"precio", "porcentaje_comision", "categoria_id"}
                  else valor for campo, valor in cambios.items()}
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "SERVICIOS",
                            "Servicio", str(servicio.id), anterior, nuevos)
        self.db.commit()
        return self.obtener(servicio.id)

    def cambiar_estado(self, servicio_id: uuid.UUID, estado: str,
                       actor: Usuario) -> Servicio:
        servicio = self.obtener(servicio_id)
        anterior = servicio.estado
        servicio.estado = estado
        self.repo.guardar(servicio)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "SERVICIOS",
                            "Servicio", str(servicio.id), {"estado": anterior},
                            {"estado": estado})
        self.db.commit()
        return self.obtener(servicio.id)

    def eliminar(self, servicio_id: uuid.UUID, actor: Usuario) -> None:
        servicio = self.obtener(servicio_id)
        registrar_auditoria(self.db, actor.id, AccionAuditoria.ELIMINAR, "SERVICIOS",
                            "Servicio", str(servicio.id),
                            valor_anterior={"nombre": servicio.nombre})
        try:
            self.db.delete(servicio)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException(
                "No se puede eliminar el servicio porque tiene registros relacionados; inactívelo"
            ) from exc
