"""
Manejadores globales de excepciones.
Traducen las excepciones de la aplicación y de terceros (SQLAlchemy, Pydantic)
en respuestas HTTP JSON consistentes para el frontend.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppException

logger = logging.getLogger("app.errors")


def _build_error_response(status_code: int, error_code: str, message: str, details=None) -> JSONResponse:
    """Construye una respuesta de error homogénea para toda la API."""
    body = {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details,
    }
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores globales de excepciones en la instancia de FastAPI."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("AppException en %s: %s", request.url.path, exc.message)
        return _build_error_response(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.info("Error de validación en %s: %s", request.url.path, exc.errors())
        return _build_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Los datos enviados no son válidos",
            details=exc.errors(),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error("Error de integridad en %s: %s", request.url.path, str(exc.orig))
        return _build_error_response(
            status.HTTP_409_CONFLICT,
            "INTEGRITY_ERROR",
            "La operación viola una restricción de integridad de datos (duplicado o relación inválida)",
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        logger.error("Error de base de datos en %s: %s", request.url.path, str(exc))
        return _build_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "DATABASE_ERROR",
            "Ocurrió un error al comunicarse con la base de datos",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Error no controlado en %s", request.url.path)
        return _build_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "Ocurrió un error interno inesperado en el servidor",
        )
