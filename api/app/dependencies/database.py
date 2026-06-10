from typing import AsyncGenerator
import asyncmy
from app.core.excepciones import BDException
from app.core.settings import settings

DB_CONFIG = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "database": settings.DB_NAME,
    "connect_timeout": settings.DB_CONNECTION_TIMEOUT,
}

_pool: asyncmy.Pool | None = None


async def crear_pool_conexiones() -> asyncmy.Pool:
    global _pool
    try:
        _pool = await asyncmy.create_pool(
            minsize=1,
            maxsize=settings.DB_POOL_SIZE,
            autocommit=False,
            **DB_CONFIG,
        )
        return _pool
    except (asyncmy.errors.MySQLError, OSError, RuntimeError) as e:
        raise BDException(
            descripcion_interna="No se pudo crear el pool de la base de datos. Detalle: "
            + str(e),
        ) from e


async def cerrar_pool_conexiones() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def obtener_conexion_bd() -> AsyncGenerator[asyncmy.Connection, None]:
    global _pool
    if _pool is None:
        raise BDException(
            descripcion_interna="El pool de conexiones de base de datos no está inicializado."
        )

    async with _pool.acquire() as conexion:
        await conexion.begin()
        try:
            yield conexion
            await conexion.commit()
        except Exception:
            await conexion.rollback()
            raise
