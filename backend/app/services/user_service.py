"""
Servicio de aplicación para la gestión de usuarios (CRUD administrativo).
Contiene las reglas de negocio: unicidad de correo, validación de rol,
generación de contraseñas temporales y registro de auditoría.
"""
import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.constants import AccionAuditoria, EstadoGenerico
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import hash_password
from app.models.user_model import Usuario
from app.repositories.implementations.rol_repository import RolRepository
from app.repositories.implementations.usuario_repository import UsuarioRepository
from app.schemas.user_schema import (
    UsuarioActualizarRequest,
    UsuarioCrearRequest,
)
from app.services.audit_service import registrar_auditoria


class UserService:
    """Servicio de aplicación que orquesta la gestión administrativa de usuarios."""

    def __init__(self, db: Session):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.rol_repo = RolRepository(db)

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
        """Lista usuarios aplicando filtros, búsqueda y paginación."""
        return self.usuario_repo.listar(
            rol, estado, busqueda, pagina, tamano_pagina, orden_por, orden_direccion
        )

    def obtener_por_id(self, usuario_id: uuid.UUID) -> Usuario:
        """Obtiene un usuario por id o lanza NotFoundException si no existe."""
        usuario = self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise NotFoundException("El usuario solicitado no existe")
        return usuario

    def crear(self, datos: UsuarioCrearRequest, usuario_actor: Usuario) -> Usuario:
        """Crea un nuevo usuario del sistema, validando unicidad de correo y rol válido."""
        correo_normalizado = datos.correo.lower().strip()
        if self.usuario_repo.obtener_por_correo(correo_normalizado):
            raise ConflictException(f"Ya existe un usuario registrado con el correo {correo_normalizado}")

        rol = self.rol_repo.obtener_por_nombre(datos.rol)
        if not rol:
            raise ValidationException(f"El rol '{datos.rol}' no existe en el sistema")

        nuevo_usuario = Usuario(
            nombre_completo=datos.nombre_completo.strip(),
            correo=correo_normalizado,
            password_hash=hash_password(datos.password),
            rol_id=rol.id,
            telefono=datos.telefono,
            estado=EstadoGenerico.ACTIVO,
            created_by=usuario_actor.id,
        )
        usuario_creado = self.usuario_repo.crear(nuevo_usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario_actor.id,
            accion=AccionAuditoria.CREAR,
            modulo="USUARIOS",
            entidad="Usuario",
            entidad_id=str(usuario_creado.id),
            valor_nuevo={"correo": usuario_creado.correo, "rol": rol.nombre},
        )
        self.db.commit()
        return usuario_creado

    def actualizar(
        self, usuario_id: uuid.UUID, datos: UsuarioActualizarRequest, usuario_actor: Usuario
    ) -> Usuario:
        """Actualiza los datos editables de un usuario existente."""
        usuario = self.obtener_por_id(usuario_id)
        valor_anterior = {
            "nombre_completo": usuario.nombre_completo,
            "telefono": usuario.telefono,
        }

        if datos.nombre_completo is not None:
            usuario.nombre_completo = datos.nombre_completo.strip()
        if datos.telefono is not None:
            usuario.telefono = datos.telefono
        if datos.avatar_url is not None:
            usuario.avatar_url = datos.avatar_url
        usuario.updated_by = usuario_actor.id

        usuario_actualizado = self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario_actor.id,
            accion=AccionAuditoria.EDITAR,
            modulo="USUARIOS",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_anterior=valor_anterior,
            valor_nuevo={"nombre_completo": usuario.nombre_completo, "telefono": usuario.telefono},
        )
        self.db.commit()
        return usuario_actualizado

    def cambiar_estado(self, usuario_id: uuid.UUID, nuevo_estado: str, usuario_actor: Usuario) -> Usuario:
        """Activa o inactiva un usuario. No permite que un usuario se inactive a sí mismo."""
        if usuario_id == usuario_actor.id and nuevo_estado == EstadoGenerico.INACTIVO:
            raise ValidationException("No puede inactivar su propia cuenta")

        usuario = self.obtener_por_id(usuario_id)
        estado_anterior = usuario.estado
        usuario.estado = nuevo_estado
        usuario.updated_by = usuario_actor.id
        usuario_actualizado = self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario_actor.id,
            accion=AccionAuditoria.EDITAR,
            modulo="USUARIOS",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_anterior={"estado": estado_anterior},
            valor_nuevo={"estado": nuevo_estado},
        )
        self.db.commit()
        return usuario_actualizado

    def cambiar_rol(self, usuario_id: uuid.UUID, nuevo_rol: str, usuario_actor: Usuario) -> Usuario:
        """Cambia el rol de un usuario existente."""
        usuario = self.obtener_por_id(usuario_id)
        rol = self.rol_repo.obtener_por_nombre(nuevo_rol)
        if not rol:
            raise ValidationException(f"El rol '{nuevo_rol}' no existe en el sistema")

        rol_anterior = usuario.rol.nombre
        usuario.rol_id = rol.id
        usuario.updated_by = usuario_actor.id
        usuario_actualizado = self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario_actor.id,
            accion=AccionAuditoria.EDITAR,
            modulo="USUARIOS",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_anterior={"rol": rol_anterior},
            valor_nuevo={"rol": rol.nombre},
        )
        self.db.commit()
        return usuario_actualizado

    def restablecer_password(self, usuario_id: uuid.UUID, usuario_actor: Usuario) -> str:
        """
        Restablece la contraseña de un usuario generando una contraseña temporal
        aleatoria. El usuario deberá cambiarla en su próximo inicio de sesión.
        """
        usuario = self.obtener_por_id(usuario_id)
        password_temporal = secrets.token_urlsafe(9)

        usuario.password_hash = hash_password(password_temporal)
        usuario.debe_cambiar_password = True
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.updated_by = usuario_actor.id
        self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario_actor.id,
            accion=AccionAuditoria.EDITAR,
            modulo="USUARIOS",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_nuevo={"accion": "restablecimiento_password_administrativo"},
        )
        self.db.commit()
        return password_temporal
