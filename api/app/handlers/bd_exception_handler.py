"""
Handler global para `BDException` (fallo de comunicación con la BD).

Responde 503 con un mensaje genérico para no filtrar detalles del motor
(host, puerto, error específico) al cliente. La `descripcion_interna` queda
en los logs.
"""

from logging import getLogger

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.excepciones import BDException

logger = getLogger(__name__)


async def bd_exception_handler(_request: Request, exc: BDException) -> JSONResponse:
    """Loggea + devuelve `503 Service Unavailable` con shape de error estándar."""
    logger.error("BDException: %s", exc.descripcion_interna)

    error_payload: dict = {
        "code": "server_error",
        "message": exc.message,
        "details": None,
    }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": error_payload,
        },
    )
