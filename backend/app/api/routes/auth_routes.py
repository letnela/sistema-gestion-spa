"""
Rutas REST del módulo de autenticación.
No contienen lógica de negocio: delegan todo a AuthService.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, obtener_ip_cliente, obtener_navegador_cliente
from app.database.session import get_db
from app.models.user_model import Usuario
from app.schemas.auth_schema import (
    CambiarPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RestablecerPasswordRequest,
    SolicitarRecuperacionRequest,
    TokenResponse,
    UsuarioPerfilResponse,
    RegistroClienteRequest,
)
from app.schemas.common_schema import RespuestaMensaje
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(datos: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica a un usuario con correo y contraseña, y retorna sus tokens JWT."""
    servicio = AuthService(db)
    ip = obtener_ip_cliente(request)
    navegador = obtener_navegador_cliente(request)
    return servicio.login(datos, ip, navegador)




@router.post("/client-register", response_model=TokenResponse, status_code=201, summary="Registrar cuenta de cliente")
def registrar_cliente(datos: RegistroClienteRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    servicio = AuthService(db)
    usuario = servicio.registrar_cliente(datos)
    return servicio.login(LoginRequest(correo=datos.correo, password=datos.password), obtener_ip_cliente(request), obtener_navegador_cliente(request))


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token de acceso")
def refrescar_token(datos: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Genera un nuevo par de tokens a partir de un refresh token válido."""
    servicio = AuthService(db)
    return servicio.refrescar_token(datos.refresh_token)


@router.post("/logout", response_model=RespuestaMensaje, summary="Cerrar sesión")
def logout(current_user: Usuario = Depends(get_current_user)) -> RespuestaMensaje:
    """
    Cierra la sesión del usuario actual. Dado que el sistema usa JWT sin estado,
    el logout real ocurre en el cliente al descartar los tokens; este endpoint
    existe para fines de auditoría y para clientes que deseen confirmarlo.
    """
    return RespuestaMensaje(message="Sesión cerrada correctamente")


@router.get("/me", response_model=UsuarioPerfilResponse, summary="Obtener perfil propio")
def obtener_perfil(current_user: Usuario = Depends(get_current_user)) -> UsuarioPerfilResponse:
    """Retorna los datos del usuario actualmente autenticado."""
    return UsuarioPerfilResponse(
        id=current_user.id,
        nombre_completo=current_user.nombre_completo,
        correo=current_user.correo,
        rol=current_user.rol.nombre,
        telefono=current_user.telefono,
        avatar_url=current_user.avatar_url,
        ultimo_login=current_user.ultimo_login,
        empleado_id=current_user.empleado.id if current_user.empleado else None,
        cliente_id=current_user.cliente_id,
    )


@router.put("/change-password", response_model=RespuestaMensaje, summary="Cambiar contraseña propia")
def cambiar_password(
    datos: CambiarPasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RespuestaMensaje:
    """Permite al usuario autenticado cambiar su propia contraseña."""
    servicio = AuthService(db)
    servicio.cambiar_password(current_user, datos.password_actual, datos.password_nuevo)
    return RespuestaMensaje(message="Contraseña actualizada correctamente")


@router.post(
    "/forgot-password", response_model=RespuestaMensaje, summary="Solicitar recuperación de contraseña"
)
def solicitar_recuperacion(
    datos: SolicitarRecuperacionRequest, db: Session = Depends(get_db)
) -> RespuestaMensaje:
    """
    Genera un token de recuperación de contraseña si el correo existe.
    Siempre responde el mismo mensaje genérico, exista o no el correo,
    para no revelar qué correos están registrados en el sistema.
    """
    servicio = AuthService(db)
    servicio.solicitar_recuperacion(datos.correo)
    return RespuestaMensaje(
        message="Si el correo está registrado, recibirá instrucciones para recuperar su contraseña"
    )


@router.post("/reset-password", response_model=RespuestaMensaje, summary="Restablecer contraseña con token")
def restablecer_password(
    datos: RestablecerPasswordRequest, db: Session = Depends(get_db)
) -> RespuestaMensaje:
    """Restablece la contraseña de un usuario a partir de un token de recuperación válido."""
    servicio = AuthService(db)
    servicio.restablecer_password(datos.token, datos.password_nuevo)
    return RespuestaMensaje(message="Contraseña restablecida correctamente")
