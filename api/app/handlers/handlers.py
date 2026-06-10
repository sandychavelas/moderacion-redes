"""
Registro central de exception handlers de FastAPI.

Importar y llamar `register_exception_handlers(app)` una sola vez al arranque.
Cada handler vive en su propio módulo (`app/handlers/*.py`) para mantener
las responsabilidades separadas.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from app.core.excepciones import AppException, BDException, ServerException
from app.handlers.app_exception_handler import app_exception_handler
from app.handlers.bd_exception_handler import bd_exception_handler
from app.handlers.rate_limit_exceeded_handler import rate_limit_exceeded_handler
from app.handlers.server_exception_handler import server_exception_handler
from app.handlers.unhandled_exception_handler import unhandled_exception_handler
from app.handlers.validation_exception_handler import validation_exception_handler


def register_exception_handlers(app: FastAPI) -> None:
    """
    Asocia cada tipo de excepción con su handler dedicado.

    Orden de prioridad (los más específicos primero):
    - `AppException`: errores de negocio (4xx con `code`/`message`).
    - `BDException`: errores de BD (503).
    - `ServerException`: errores de configuración del servidor en runtime (500).
    - `RequestValidationError`: input malformado (422 con detalle de campos).
    - `RateLimitExceeded`: demasiados requests (429).
    - `Exception`: catch-all (500 sin detalles al cliente).
    """
    app.exception_handler(AppException)(app_exception_handler)
    app.exception_handler(BDException)(bd_exception_handler)
    app.exception_handler(ServerException)(server_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(Exception)(unhandled_exception_handler)
    app.exception_handler(RateLimitExceeded)(rate_limit_exceeded_handler)
