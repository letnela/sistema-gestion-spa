"""Interfaz abstracta del repositorio de usuarios (patrón Repository)."""
import uuid
from abc import ABC, abstractmethod

from app.models.user_model import Usuario


class IUsuarioRepository(ABC):
    """Contrato que debe cumplir cualquier implementación de acceso a datos de Usuario."""

    @abstractmethod
    def obtener_por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        """Obtiene un usuario por su identificador único."""
        raise NotImplementedError

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None:
        """Obtiene un usuario por su dirección de correo electrónico."""
        raise NotImplementedError

    @abstractmethod
    def listar(
        self,
        rol: str | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int,
        tamano_pagina: int,
        orden_por: str | None,
        orden_direccion: str,
    ) -> tuple[list[Usuario], int]:
        """Lista usuarios aplicando filtros, búsqueda, orden y paginación."""
        raise NotImplementedError

    @abstractmethod
    def crear(self, usuario: Usuario) -> Usuario:
        """Persiste un nuevo usuario."""
        raise NotImplementedError

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario:
        """Persiste los cambios realizados sobre un usuario existente."""
        raise NotImplementedError
