"""
Utilidad para el manejo explícito de transacciones en operaciones
que requieren atomicidad entre múltiples repositorios (por ejemplo,
una venta que descuenta inventario y genera un pago en la misma operación).
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager que agrupa varias operaciones en una única transacción.
    Si ocurre una excepción dentro del bloque, se revierte todo el trabajo
    realizado; si finaliza correctamente, se hace commit una única vez.

    Uso:
        with transaction(db) as tx:
            tx.add(objeto_1)
            tx.add(objeto_2)
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
