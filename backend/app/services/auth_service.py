"""
Servicio de aplicación para autenticación.
Contiene toda la lógica de negocio de login, generación de tokens JWT,
bloqueo temporal de cuentas por intentos fallidos, cambio y recuperación
de contraseña. Los routers NO deben contener esta lógica.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import AccionAuditoria, EstadoGenerico, RolesSistema
from app.core.exceptions import (
    AccountLockedException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user_model import IntentoLogin, Usuario
from app.models.client_model import Cliente
from app.models.role_model import Rol
from app.repositories.implementations.usuario_repository import UsuarioRepository
from app.schemas.auth_schema import LoginRequest, TokenResponse, RegistroClienteRequest
from app.services.audit_service import registrar_auditoria


class AuthService:
    """Servicio de aplicación que orquesta toda la lógica de autenticación."""

    def __init__(self, db: Session):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)

    def registrar_cliente(self, datos: RegistroClienteRequest) -> Usuario:
        correo = str(datos.correo).lower().strip()
        if self.usuario_repo.obtener_por_correo(correo):
            raise ValidationException("Ya existe una cuenta con ese correo")
        if datos.documento and self.db.query(Cliente).filter(Cliente.documento == datos.documento).first():
            raise ValidationException("Ya existe un cliente con ese documento")
        rol = self.db.query(Rol).filter(Rol.nombre == RolesSistema.CLIENTE).first()
        if not rol:
            rol = Rol(nombre=RolesSistema.CLIENTE, descripcion="Portal de autoservicio del cliente")
            self.db.add(rol); self.db.flush()
        cliente = Cliente(nombres=datos.nombres.strip(), apellidos=datos.apellidos.strip(), correo=correo, telefono=datos.telefono, documento=datos.documento, estado=EstadoGenerico.ACTIVO)
        self.db.add(cliente); self.db.flush()
        usuario = Usuario(nombre_completo=f"{cliente.nombres} {cliente.apellidos}", correo=correo, password_hash=hash_password(datos.password), rol_id=rol.id, cliente_id=cliente.id, estado=EstadoGenerico.ACTIVO)
        self.db.add(usuario); self.db.commit(); self.db.refresh(usuario)
        return usuario

    def login(self, datos: LoginRequest, ip_origen: str | None, navegador: str | None) -> TokenResponse:
        """
        Autentica a un usuario con correo y contraseña.

        Reglas de negocio:
        - Si la cuenta está bloqueada temporalmente, se rechaza el intento.
        - Cada intento fallido incrementa el contador; al alcanzar el máximo
          configurado, la cuenta se bloquea por `LOGIN_LOCKOUT_MINUTES`.
        - Un login exitoso reinicia el contador de intentos fallidos.
        - Todo intento (exitoso o no) se registra en `intentos_login`.
        """
        usuario = self.usuario_repo.obtener_por_correo(datos.correo)

        if usuario and self._cuenta_esta_bloqueada(usuario):
            self._registrar_intento(usuario.id, datos.correo, False, ip_origen, navegador)
            raise AccountLockedException(
                f"La cuenta está bloqueada hasta {usuario.bloqueado_hasta.isoformat()} "
                "por múltiples intentos fallidos"
            )

        credenciales_validas = usuario is not None and verify_password(datos.password, usuario.password_hash)

        if not credenciales_validas:
            if usuario:
                self._registrar_intento_fallido(usuario)
            self._registrar_intento(
                usuario.id if usuario else None, datos.correo, False, ip_origen, navegador
            )
            raise UnauthorizedException("Correo o contraseña incorrectos")

        if usuario.estado != EstadoGenerico.ACTIVO:
            self._registrar_intento(usuario.id, datos.correo, False, ip_origen, navegador)
            raise UnauthorizedException("El usuario se encuentra inactivo, contacte al administrador")

        # Login exitoso: reiniciar contador de intentos fallidos
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.ultimo_login = datetime.now(timezone.utc)
        self.usuario_repo.actualizar(usuario)

        self._registrar_intento(usuario.id, datos.correo, True, ip_origen, navegador)
        registrar_auditoria(
            self.db,
            usuario_id=usuario.id,
            accion=AccionAuditoria.LOGIN,
            modulo="AUTH",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            ip_origen=ip_origen,
            navegador=navegador,
        )
        self.db.commit()

        return self._generar_tokens(usuario)

    def refrescar_token(self, refresh_token: str) -> TokenResponse:
        """Genera un nuevo par de tokens a partir de un refresh token válido."""
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise UnauthorizedException("El token de refresco es inválido o expiró") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedException("El token proporcionado no es un token de refresco")

        usuario = self.usuario_repo.obtener_por_id(uuid.UUID(payload["sub"]))
        if not usuario or usuario.estado != EstadoGenerico.ACTIVO:
            raise UnauthorizedException("Usuario no válido o inactivo")

        return self._generar_tokens(usuario)

    def cambiar_password(self, usuario: Usuario, password_actual: str, password_nuevo: str) -> None:
        """Cambia la contraseña de un usuario autenticado, validando la contraseña actual."""
        if not verify_password(password_actual, usuario.password_hash):
            raise ValidationException("La contraseña actual no es correcta")

        usuario.password_hash = hash_password(password_nuevo)
        usuario.debe_cambiar_password = False
        self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario.id,
            accion=AccionAuditoria.EDITAR,
            modulo="AUTH",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_nuevo={"accion": "cambio_password"},
        )
        self.db.commit()

    def solicitar_recuperacion(self, correo: str) -> str | None:
        """
        Genera un token de recuperación de contraseña válido por 1 hora.
        Retorna None si el correo no existe, sin revelar esa información al llamador HTTP
        (el router siempre debe responder con un mensaje genérico).
        """
        usuario = self.usuario_repo.obtener_por_correo(correo)
        if not usuario:
            return None

        token = secrets.token_urlsafe(32)
        usuario.reset_password_token = token
        usuario.reset_password_expira = datetime.now(timezone.utc) + timedelta(hours=1)
        self.usuario_repo.actualizar(usuario)
        return token

    def restablecer_password(self, token: str, password_nuevo: str) -> None:
        """Restablece la contraseña de un usuario a partir de un token de recuperación válido."""
        usuario = self.db.query(Usuario).filter(Usuario.reset_password_token == token).first()

        if not usuario or not usuario.reset_password_expira:
            raise ValidationException("El token de recuperación no es válido")

        expira = usuario.reset_password_expira
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        if expira < datetime.now(timezone.utc):
            raise ValidationException("El token de recuperación ha expirado")

        usuario.password_hash = hash_password(password_nuevo)
        usuario.reset_password_token = None
        usuario.reset_password_expira = None
        usuario.debe_cambiar_password = False
        self.usuario_repo.actualizar(usuario)

        registrar_auditoria(
            self.db,
            usuario_id=usuario.id,
            accion=AccionAuditoria.EDITAR,
            modulo="AUTH",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            valor_nuevo={"accion": "restablecimiento_password"},
        )
        self.db.commit()

    # ------------------------------------------------------------------
    # Métodos privados de apoyo
    # ------------------------------------------------------------------

    def _generar_tokens(self, usuario: Usuario) -> TokenResponse:
        """Genera el par de tokens access/refresh para un usuario ya autenticado."""
        claims = {"rol": usuario.rol.nombre, "correo": usuario.correo}
        access_token = create_access_token(str(usuario.id), claims)
        refresh_token = create_refresh_token(str(usuario.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expira_en_minutos=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    def _cuenta_esta_bloqueada(self, usuario: Usuario) -> bool:
        """Determina si la cuenta de un usuario está actualmente bloqueada."""
        if not usuario.bloqueado_hasta:
            return False
        bloqueado_hasta = usuario.bloqueado_hasta
        if bloqueado_hasta.tzinfo is None:
            bloqueado_hasta = bloqueado_hasta.replace(tzinfo=timezone.utc)
        return bloqueado_hasta > datetime.now(timezone.utc)

    def _registrar_intento_fallido(self, usuario: Usuario) -> None:
        """Incrementa el contador de intentos fallidos y bloquea la cuenta si se supera el máximo."""
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= settings.MAX_LOGIN_ATTEMPTS:
            usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
        self.usuario_repo.actualizar(usuario)

    def _registrar_intento(
        self,
        usuario_id: uuid.UUID | None,
        correo_intentado: str,
        exitoso: bool,
        ip_origen: str | None,
        navegador: str | None,
    ) -> None:
        """Persiste un registro en la tabla `intentos_login`."""
        intento = IntentoLogin(
            usuario_id=usuario_id,
            correo_intentado=correo_intentado.lower().strip(),
            exitoso=exitoso,
            ip_origen=ip_origen,
            navegador=navegador,
            fecha=datetime.now(timezone.utc),
        )
        self.db.add(intento)
        self.db.commit()
