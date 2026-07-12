"""Interfaz abstracta del repositorio de clientes."""
import uuid
from abc import ABC, abstractmethod

from app.models.client_model import Cliente


class IClienteRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, cliente_id: uuid.UUID) -> Cliente | None: ...

    @abstractmethod
    def obtener_por_documento(self, documento: str) -> Cliente | None: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Cliente | None: ...

    @abstractmethod
    def listar(self, estado: str | None, busqueda: str | None, pagina: int,
               tamano_pagina: int, orden_por: str | None,
               orden_direccion: str) -> tuple[list[Cliente], int]: ...

    @abstractmethod
    def crear(self, cliente: Cliente) -> Cliente: ...

    @abstractmethod
    def actualizar(self, cliente: Cliente) -> Cliente: ...
