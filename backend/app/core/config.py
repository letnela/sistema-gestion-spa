"""
Configuración central de la aplicación.
Carga variables de entorno desde el archivo .env y las expone
como un objeto de configuración fuertemente tipado.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación, cargada desde variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "peluqueria"
    DB_USER: str = "peluqueria_user"
    DB_PASSWORD: str = "Sinley123."
    DATABASE_URL: str = (
        "postgresql+psycopg2://peluqueria_user:Sinley123.@localhost:5432/peluqueria"
    )

    # Seguridad / JWT
    SECRET_KEY: str = "cambiar_esta_clave_en_produccion_por_una_muy_segura_y_larga"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Aplicación
    APP_NAME: str = "Sistema de Gestión de Salón de Belleza"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Seguridad de login
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # Paginación
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Asistente virtual (IA) — opcional. Elige el proveedor con AI_PROVIDER y configura
    # solo la clave de ese proveedor. Sin ninguna clave configurada, el chat queda
    # deshabilitado (responde con un mensaje claro, no se rompe).
    AI_PROVIDER: str = "local"  # "anthropic" | "nvidia" | "groq" | "n8n"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"

    # NVIDIA NIM (build.nvidia.com) — API compatible con OpenAI, tiene modelos gratis
    # para probar. No soporta imágenes en esta integración (usa "anthropic" para eso).
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "meta/llama-3.1-8b-instruct"

    # Groq (console.groq.com) — API compatible con OpenAI, registro simple con correo,
    # plan gratis generoso y respuestas muy rápidas. Tampoco soporta imágenes aquí.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # Rendimiento y resiliencia del chat
    CHAT_PROVIDER_TIMEOUT_SECONDS: float = 8.0
    CHAT_MAX_HISTORY_MESSAGES: int = 10
    CHAT_FAST_LOCAL_ENABLED: bool = True

    # Orquestación externa del chat vía n8n (opcional). Si AI_PROVIDER=n8n, el chat llama
    # a tu flujo de n8n en vez de llamar a un proveedor de IA directamente desde aquí.
    N8N_WEBHOOK_URL: str = ""
    N8N_WEBHOOK_SECRET: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte la cadena de orígenes CORS en una lista de strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Retorna una instancia cacheada de la configuración.
    Se usa lru_cache para no releer el .env en cada llamada.
    """
    return Settings()


settings = get_settings()
