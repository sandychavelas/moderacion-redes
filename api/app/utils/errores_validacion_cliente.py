"""
Formateo de errores Pydantic para respuestas JSON al cliente.

Misma forma que usa `validation_exception_handler` (`{"field": str, "message": str}`)
para que el front pueda reutilizar lógica de mapeo a inputs.
"""

from typing import Any


def campos_para_cliente_desde_errores_pydantic(
    errores: list[dict[str, Any]],
) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for err in errores:
        loc = err.get("loc") or []
        msg = (err.get("msg") or "").strip()
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :].strip()

        if isinstance(loc, (list, tuple)) and len(loc) >= 2:
            field = ".".join(str(x) for x in loc[1:])
        elif isinstance(loc, (list, tuple)) and len(loc) == 1:
            field = str(loc[0])
        else:
            field = "unknown"

        fields.append({"field": field, "message": msg})

    return fields
