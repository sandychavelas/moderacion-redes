"""
Handler para errores de validación de Pydantic (`RequestValidationError`).

Convierte la lista cruda de errores de Pydantic en un formato consistente:

```json
{
  "error": {
    "code": "validation_error",
    "message": "...",
    "fields": [{"field": "correo_usuario", "message": "value is not a valid email address"}]
  }
}
```

El frontend puede mapear `fields` a mensajes por input específico.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.errores_validacion_cliente import (
    campos_para_cliente_desde_errores_pydantic,
)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Aplana los errores de Pydantic a `{field, message}`.

    Notas:
        - Quita el prefijo `"Value error, "` que Pydantic agrega a errores
          de validadores custom, para que el mensaje quede más limpio.
        - Si `loc` viene con varios niveles (anidados), los une con `.`.
    """
    fields = campos_para_cliente_desde_errores_pydantic(exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Los datos enviados no son válidos, revise los campos y vuelva a intentarlo.",
                "fields": fields,
            }
        },
    )
