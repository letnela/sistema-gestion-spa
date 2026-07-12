"""
Configuración del motor de base de datos y de las sesiones de SQLAlchemy.
Expone `get_db`, una dependencia de FastAPI que entrega una sesión por request
y garantiza su cierre correcto.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI que provee una sesión de base de datos por cada
    request y la cierra automáticamente al finalizar, haciendo rollback
    si ocurrió alguna excepción no controlada.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
