"""Repositorio de acceso a datos para la entidad Rol."""
from sqlalchemy.orm import Session

from app.models.role_model import Rol


class RolRepository:
    """Repositorio simple de acceso a datos para Rol (catálogo de solo lectura en runtime)."""

    def __init__(self, db: Session):
        self.db = db

    def obtener_por_nombre(self, nombre: str) -> Rol | None:
        """Obtiene un rol por su nombre exacto."""
        return self.db.query(Rol).filter(Rol.nombre == nombre).first()

    def listar_todos(self) -> list[Rol]:
        """Lista todos los roles disponibles en el sistema."""
        return self.db.query(Rol).order_by(Rol.nombre).all()
