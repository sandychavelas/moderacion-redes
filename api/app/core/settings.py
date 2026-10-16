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

    origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
    ]

    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url.rstrip("/"))

    if raw:
        for o in raw.split(","):
            val = o.strip().rstrip("/")
            if val and val not in origins:
                origins.append(val)

    return origins


class Settings:
    PROJECT_NAME: str = "Moderación de contenido en redes sociales"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API para el Sistema de Moderación de contenido en redes sociales"

    ENV: str = os.getenv("ENV", "production")
    DOCS_ENABLED: bool = os.getenv("DOCS_ENABLED", "true").lower() == "true"
    CORS_ORIGINS: List[str] = _obtener_cors_origins()
    COOKIES_SECURE: bool = os.getenv("COOKIES_SECURE", "false").lower() == "true"
    COOKIES_SAMESITE: str = os.getenv("COOKIES_SAMESITE", "lax")

    # Compatibilidad transparente con Railway (MYSQLHOST / MYSQL_HOST, MYSQLDATABASE / MYSQL_DATABASE, etc.)
    DB_HOST: str = os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST") or os.getenv("MARIADB_HOST") or "localhost"
    DB_PORT: int = _obtener_int_env("DB_PORT", _obtener_int_env("MYSQLPORT", _obtener_int_env("MYSQL_PORT", 3306)))
    DB_USER: str = os.getenv("DB_USER") or os.getenv("MYSQLUSER") or os.getenv("MYSQL_USER") or os.getenv("MARIADB_USER") or "root"
    DB_PASSWORD: str = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_PASSWORD") or os.getenv("MARIADB_PASSWORD") or ""
    DB_NAME: str = (
        os.getenv("DB_NAME")
        or os.getenv("MYSQLDATABASE")
        or os.getenv("MYSQL_DATABASE")
        or os.getenv("MARIADB_DATABASE")
        or "moderacionbd"
    )
    DB_POOL_SIZE: int = _obtener_int_env("DB_POOL_SIZE", 5)
    DB_CONNECTION_TIMEOUT: int = _obtener_int_env("DB_CONNECTION_TIMEOUT", 10)

    # Configuración de DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")


settings = Settings()
