"""
Servicio de auditoría.
Provee una función centralizada para registrar acciones de crear, editar,
eliminar, cancelar, pagar y login en la tabla `auditoria`, evitando repetir
esta lógica en cada servicio de negocio.
"""
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_model import Auditoria


def _serializar(valor: Any) -> dict | None:
    """Convierte un objeto (dict, modelo Pydantic, etc.) a un dict serializable en JSONB."""
    if valor is None:
        return None
    if isinstance(valor, dict):
        return valor
    if hasattr(valor, "model_dump"):
        return valor.model_dump(mode="json")
    return dict(valor)


def registrar_auditoria(
    db: Session,
    usuario_id: uuid.UUID | None,
    accion: str,
    modulo: str,
    entidad: str,
    entidad_id: str | None = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    ip_origen: str | None = None,
    navegador: str | None = None,
) -> Auditoria:
    """
    Registra una entrada de auditoría. No hace commit por sí mismo cuando se
    invoca dentro de una transacción más amplia; el llamador decide si hace
    commit inmediatamente o como parte de una operación mayor.
    """
    entrada = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        modulo=modulo,
        entidad=entidad,
        entidad_id=entidad_id,
        valor_anterior=_serializar(valor_anterior),
        valor_nuevo=_serializar(valor_nuevo),
        ip_origen=ip_origen,
        navegador=navegador,
    )
    db.add(entrada)
    db.flush()
    return entrada
