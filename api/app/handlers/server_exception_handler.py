"""
Handler para `ServerException` (configuración inválida del servidor).

En la práctica, `ServerException` se lanza durante el `lifespan` y aborta el
arranque antes de aceptar requests. Este handler existe como red de
seguridad por si alguna ruta lanza la excepción en runtime; lo más probable
es que nunca se ejecute.
"""

from logging import getLogger

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.excepciones import ServerException

logger = getLogger(__name__)


def server_exception_handler(_request: Request, exc: ServerException) -> JSONResponse:
    """Loggea + devuelve `500` con shape de error estándar."""
    logger.error("ServerException: %s", exc.descripcion_interna)

    error_payload: dict = {
        "code": "server_error",
        "message": exc.message,
        "details": None,
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error_payload},
    )
