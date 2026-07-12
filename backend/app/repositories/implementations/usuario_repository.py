"""Implementación con SQLAlchemy del repositorio de usuarios."""
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.role_model import Rol
from app.models.user_model import Usuario
from app.repositories.interfaces.usuario_repository_interface import IUsuarioRepository
from app.utils.pagination import paginar_query


class UsuarioRepository(IUsuarioRepository):
    """Repositorio de acceso a datos para la entidad Usuario, basado en SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        """Obtiene un usuario por su identificador único, cargando su rol."""
        return (
            self.db.query(Usuario)
            .options(joinedload(Usuario.rol))
            .filter(Usuario.id == usuario_id)
            .first()
        )

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        """Obtiene un usuario por su correo electrónico, cargando su rol."""
        return (
            self.db.query(Usuario)
            .options(joinedload(Usuario.rol))
            .filter(Usuario.correo == correo.lower().strip())
            .first()
        )

    def listar(
        self,
        rol: str | None = None,
        estado: str | None = None,
        busqueda: str | None = None,
        pagina: int = 1,
        tamano_pagina: int = 20,
        orden_por: str | None = "created_at",
        orden_direccion: str = "desc",
    ) -> tuple[list[Usuario], int]:
        """Lista usuarios aplicando filtros por rol, estado y búsqueda de texto libre."""
        query = self.db.query(Usuario).options(joinedload(Usuario.rol))

        if rol:
            query = query.join(Rol).filter(Rol.nombre == rol)
        if estado:
            query = query.filter(Usuario.estado == estado)
        if busqueda:
            texto = f"%{busqueda.strip()}%"
            query = query.filter(
                or_(Usuario.nombre_completo.ilike(texto), Usuario.correo.ilike(texto))
            )

        return paginar_query(query, pagina, tamano_pagina, orden_por, orden_direccion, Usuario)

    def crear(self, usuario: Usuario) -> Usuario:
        """Persiste un nuevo usuario en la base de datos."""
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def actualizar(self, usuario: Usuario) -> Usuario:
        """Persiste los cambios realizados sobre un usuario existente."""
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
