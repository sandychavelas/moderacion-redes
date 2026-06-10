import os
from typing import List


def _obtener_int_env(nombre: str, default: int) -> int:
    raw = os.getenv(nombre)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _obtener_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()

    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]

    origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    return origins


class Settings:
    PROJECT_NAME: str = "Moderación de contenido en redes sociales"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API para el Sistema de Moderación de contenido en redes sociales"

    ENV: str = os.getenv("ENV", "development")
    DOCS_ENABLED: bool = os.getenv("DOCS_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: List[str] = _obtener_cors_origins()
    COOKIES_SECURE: bool = os.getenv("COOKIES_SECURE", "false").lower() == "true"
    COOKIES_SAMESITE: str = os.getenv("COOKIES_SAMESITE", "lax")

    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = _obtener_int_env("DB_PORT", 3306)
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_POOL_SIZE: int = _obtener_int_env("DB_POOL_SIZE", 5)
    DB_CONNECTION_TIMEOUT: int = _obtener_int_env("DB_CONNECTION_TIMEOUT", 10)

    # Configuración de DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")


settings = Settings()
