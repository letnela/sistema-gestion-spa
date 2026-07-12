"""Contrato del repositorio de empleados."""
from abc import ABC, abstractmethod
import uuid
from app.models.employee_model import Empleado

class IEmpleadoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, empleado_id: uuid.UUID) -> Empleado | None: ...
    @abstractmethod
    def listar(self, estado=None, cargo=None, busqueda=None, pagina=1, tamano_pagina=20,
               orden_por="created_at", orden_direccion="desc") -> tuple[list[Empleado], int]: ...
