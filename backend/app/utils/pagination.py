"""
Utilidad de paginación reusable.
Aplica paginación, ordenamiento y devuelve el total de registros sobre
cualquier Query de SQLAlchemy, evitando repetir esta lógica en cada repositorio.
"""
from typing import Any, Tuple

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query


def paginar_query(
    query: Query,
    pagina: int = 1,
    tamano_pagina: int = 20,
    orden_por: str | None = None,
    orden_direccion: str = "asc",
    modelo: Any = None,
) -> Tuple[list, int]:
    """
    Aplica paginación y ordenamiento a un Query de SQLAlchemy.

    Args:
        query: Query base ya filtrado (sin paginar).
        pagina: número de página (base 1).
        tamano_pagina: cantidad de elementos por página.
        orden_por: nombre del atributo del modelo por el cual ordenar.
        orden_direccion: 'asc' o 'desc'.
        modelo: clase del modelo ORM, requerida si se especifica `orden_por`.

    Returns:
        Tupla (items, total) con los elementos de la página solicitada y el
        total de registros que cumplen el filtro (sin paginar).
    """
    total = query.order_by(None).count()

    if orden_por and modelo is not None and hasattr(modelo, orden_por):
        columna = getattr(modelo, orden_por)
        query = query.order_by(desc(columna) if orden_direccion == "desc" else asc(columna))

    pagina = max(pagina, 1)
    tamano_pagina = max(min(tamano_pagina, 100), 1)
    offset = (pagina - 1) * tamano_pagina

    items = query.offset(offset).limit(tamano_pagina).all()
    return items, total
