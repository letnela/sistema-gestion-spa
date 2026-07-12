"""Contrato del repositorio de citas."""
from abc import ABC, abstractmethod

class ICitaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, cita_id): ...
    @abstractmethod
    def listar(self, *args, **kwargs): ...
    @abstractmethod
    def guardar(self, cita): ...
