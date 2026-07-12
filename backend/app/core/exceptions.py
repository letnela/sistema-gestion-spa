"""
Excepciones personalizadas de la aplicación.
Estas excepciones son capturadas por los manejadores globales definidos
en app.core.error_handlers y traducidas a respuestas HTTP consistentes.
"""


class AppException(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, message: str, status_code: int = 400, error_code: str = "APP_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class NotFoundException(AppException):
    """Se lanza cuando un recurso solicitado no existe."""

    def __init__(self, message: str = "El recurso solicitado no fue encontrado"):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class ConflictException(AppException):
    """Se lanza cuando existe un conflicto de datos (duplicados, estados incompatibles)."""

    def __init__(self, message: str = "Conflicto con el estado actual del recurso"):
        super().__init__(message, status_code=409, error_code="CONFLICT")


class ValidationException(AppException):
    """Se lanza cuando una regla de negocio de validación falla."""

    def __init__(self, message: str = "Los datos proporcionados no son válidos"):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR")


class UnauthorizedException(AppException):
    """Se lanza cuando la autenticación falla o el token no es válido."""

    def __init__(self, message: str = "No autorizado"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenException(AppException):
    """Se lanza cuando el usuario autenticado no tiene permisos suficientes."""

    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


class AccountLockedException(AppException):
    """Se lanza cuando una cuenta está bloqueada por intentos fallidos de login."""

    def __init__(self, message: str = "La cuenta se encuentra bloqueada temporalmente"):
        super().__init__(message, status_code=423, error_code="ACCOUNT_LOCKED")


class InsufficientStockException(AppException):
    """Se lanza cuando se intenta vender o descontar más stock del disponible."""

    def __init__(self, message: str = "Stock insuficiente para completar la operación"):
        super().__init__(message, status_code=409, error_code="INSUFFICIENT_STOCK")


class ScheduleConflictException(AppException):
    """Se lanza cuando existe un conflicto de horario o doble reserva de una cita."""

    def __init__(self, message: str = "Existe un conflicto de horario para el empleado seleccionado"):
        super().__init__(message, status_code=409, error_code="SCHEDULE_CONFLICT")
