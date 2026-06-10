from logging import getLogger
from app.core.excepciones import ServerException
from app.core.settings import settings
import os

logger = getLogger(__name__)


def validar_configuracion_bd() -> list[str]:
    errores = []

    if not settings.DB_HOST:
        errores.append("El host de la base de datos no está configurado.")
    if not settings.DB_PORT:
        errores.append("El puerto de la base de datos no está configurado.")
    if not settings.DB_USER:
        errores.append("El usuario de la base de datos no está configurado.")
    if not settings.DB_PASSWORD:
        errores.append("La contraseña de la base de datos no está configurada.")
    if not settings.DB_NAME:
        errores.append("El nombre de la base de datos no está configurado.")
    if not settings.DB_POOL_SIZE:
        errores.append("El tamaño del pool de conexiones no está configurado.")
    if not settings.DB_CONNECTION_TIMEOUT:
        errores.append("El timeout de la conexión a la base de datos no está configurado.")
    if settings.DB_POOL_SIZE < 1:
        errores.append("El tamaño del pool de conexiones no puede ser menor a 1.")
    if settings.DB_CONNECTION_TIMEOUT < 1:
        errores.append("El timeout de la conexión a la base de datos no puede ser menor a 1.")

    return errores


def validar_configuracion_cors() -> list[str]:
    errores = []

    # Con allow_credentials=True, Starlette no permite '*' en allow_origins
    if "*" in settings.CORS_ORIGINS:
        errores.append(
            "CORS_ORIGINS no puede contener '*' cuando se requiere allow_credentials (cookies/credenciales)."
        )

    return errores


def validar_configuracion_servidor() -> None:
    errores_bd = validar_configuracion_bd()
    errores_cors = validar_configuracion_cors()
    todos_los_errores = errores_bd + errores_cors

    if todos_los_errores:
        for error in todos_los_errores:
            logger.error(error)
        logger.error("La API no iniciará: configuración inválida.")
        raise ServerException(message="\n".join(todos_los_errores))
