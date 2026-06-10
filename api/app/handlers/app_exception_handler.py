import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.excepciones import AppException

logger = logging.getLogger(__name__)


def _log_app_exception(request: Request, exc: AppException) -> None:
    """
    Loggea una línea estructurada con la metadata del error.

    `descripcion_interna` se incluye si está presente; el `message` visible
    al usuario también se loggea para correlación con tickets de soporte.
    Nivel WARNING para 4xx, ERROR para 5xx.
    """
    desc = (
        exc.descripcion_interna
        if exc.descripcion_interna is not None
        else "No se agregó descripción a este error"
    )
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    linea = (
        "AppException | status=%s code=%s method=%s path=%s ip=%s ua=%s "
        "descripcion_interna=%r message_usuario=%r details=%s"
    ) % (
        exc.status_code,
        exc.code,
        request.method,
        request.url.path,
        client_ip,
        user_agent,
        desc,
        exc.message,
        exc.details,
    )

    if exc.status_code >= 500:
        logger.error(linea)
    else:
        logger.warning(linea)


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """
    Convierte un `AppException` en `JSONResponse` con shape:

    ```json
    {"error": {"code": "...", "message": "...", "details": {...}}}
    ```

    `details` solo se incluye si la excepción lo provee.
    """
    _log_app_exception(_request, exc)

    error_payload: dict = {
        "code": exc.code,
        "message": exc.message,
    }
    if exc.details:
        error_payload["details"] = exc.details

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_payload,
        },
    )

    return response
