"""Contratos de repositorio para categorías y servicios."""
import uuid
from abc import ABC, abstractmethod

from app.models.service_model import CategoriaServicio, Servicio


class ICategoriaServicioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, categoria_id: uuid.UUID) -> CategoriaServicio | None: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> CategoriaServicio | None: ...

    @abstractmethod
    def listar(self, estado: str | None, busqueda: str | None, pagina: int,
               tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[CategoriaServicio], int]: ...

    @abstractmethod
    def guardar(self, categoria: CategoriaServicio) -> CategoriaServicio: ...


class IServicioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, servicio_id: uuid.UUID) -> Servicio | None: ...

    @abstractmethod
    def obtener_por_nombre_y_categoria(self, nombre: str,
                                        categoria_id: uuid.UUID) -> Servicio | None: ...

    @abstractmethod
    def listar(self, categoria_id: uuid.UUID | None, estado: str | None,
               busqueda: str | None, precio_min: float | None, precio_max: float | None,
               pagina: int, tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[Servicio], int]: ...

    @abstractmethod
    def guardar(self, servicio: Servicio) -> Servicio: ...
