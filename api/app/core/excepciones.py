# Respuesta genérica al cliente y código compartidos (p. ej. AppException o errores no controlados).
CODIGO_ERROR_SERVIDOR_GENERICO = "server_error"
MENSAJE_ERROR_SERVIDOR_GENERICO_USUARIO = (
    "Error en el servidor, comuníquese con el administrador e intente nuevamente."
)


class ServerException(Exception):
    """
    Error grave de configuración/arranque del servidor.

    Lanzar esta excepción durante el `lifespan` de FastAPI aborta el arranque
    de la API. NO usar para errores de runtime.
    """

    def __init__(
        self,
        *,
        message: str = MENSAJE_ERROR_SERVIDOR_GENERICO_USUARIO,
        descripcion_interna: str | None = None,
    ) -> None:
        self.message = message
        self.descripcion_interna = descripcion_interna


class BDException(Exception):
    """
    Fallo en la comunicación con la base de datos.

    Se traduce a HTTP 503. El mensaje al cliente es genérico para no exponer
    detalles del motor; `descripcion_interna` se loggea para diagnóstico.
    """

    def __init__(
        self,
        *,
        message: str = MENSAJE_ERROR_SERVIDOR_GENERICO_USUARIO,
        descripcion_interna: str | None = None,
    ):
        self.message = message
        self.descripcion_interna = descripcion_interna


class AppException(Exception):
    """Error de dominio: `message` y `details` pueden exponerse al cliente; `descripcion_interna` solo para logs."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
        descripcion_interna: str | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.descripcion_interna = descripcion_interna
