"""
Esquemas comunes reutilizables en toda la API: paginación, respuestas
estándar de éxito/error y parámetros de filtrado y ordenamiento.
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ParametrosPaginacion(BaseModel):
    """Parámetros de entrada estándar para listados paginados."""

    pagina: int = Field(default=1, ge=1, description="Número de página, comienza en 1")
    tamano_pagina: int = Field(default=20, ge=1, le=100, description="Cantidad de elementos por página")
    orden_por: Optional[str] = Field(default=None, description="Campo por el cual ordenar")
    orden_direccion: Optional[str] = Field(default="asc", pattern="^(asc|desc)$")
    busqueda: Optional[str] = Field(default=None, description="Texto de búsqueda libre")


class RespuestaPaginada(BaseModel, Generic[T]):
    """Envoltorio estándar de respuesta para listados paginados."""

    items: List[T]
    total: int
    pagina: int
    tamano_pagina: int
    total_paginas: int

    @classmethod
    def crear(cls, items: List[T], total: int, pagina: int, tamano_pagina: int) -> "RespuestaPaginada[T]":
        """Construye una respuesta paginada calculando el total de páginas."""
        total_paginas = (total + tamano_pagina - 1) // tamano_pagina if tamano_pagina else 0
        return cls(items=items, total=total, pagina=pagina, tamano_pagina=tamano_pagina, total_paginas=total_paginas)


class RespuestaExito(BaseModel, Generic[T]):
    """Envoltorio estándar de respuesta exitosa con un único recurso."""

    success: bool = True
    data: T
    message: Optional[str] = None


class RespuestaMensaje(BaseModel):
    """Respuesta simple de confirmación sin datos adicionales."""

    success: bool = True
    message: str
