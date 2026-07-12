from abc import ABC, abstractmethod
import uuid

class VentaRepositoryInterface(ABC):
    @abstractmethod
    def obtener_por_id(self, venta_id: uuid.UUID): ...
    @abstractmethod
    def listar(self, *args, **kwargs): ...
    @abstractmethod
    def guardar(self, venta): ...
