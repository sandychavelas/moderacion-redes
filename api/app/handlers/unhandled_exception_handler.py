"""
Handler catch-all para excepciones NO previstas (último recurso).

Loggea el traceback completo con metadata del request y responde 500 con un
mensaje genérico. Nunca debe filtrar al cliente el stack trace o detalles
internos.
"""

import logging
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.excepciones import (
    CODIGO_ERROR_SERVIDOR_GENERICO,
    MENSAJE_ERROR_SERVIDOR_GENERICO_USUARIO,
)

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Loggea con traceback + devuelve `500 Internal Server Error`.

    El mensaje al cliente es deliberadamente genérico para no filtrar
    información sensible (paths internos, stack frames, etc.).
    """
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.error(
        "Error no controlado | type=%s method=%s path=%s ip=%s ua=%s\n%s",
        type(exc).__name__,
        request.method,
        request.url.path,
        client_ip,
        user_agent,
        tb,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": CODIGO_ERROR_SERVIDOR_GENERICO,
                "message": MENSAJE_ERROR_SERVIDOR_GENERICO_USUARIO,
                "details": None,
            }
        },
    )
