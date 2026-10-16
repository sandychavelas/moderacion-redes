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


TABLAS_DDL = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        rol ENUM('Product Owner', 'Scrum Master', 'Developer') DEFAULT 'Developer',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS productos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        sector VARCHAR(50),
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS posts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_externo VARCHAR(100) NOT NULL UNIQUE,
        texto TEXT NOT NULL,
        autor VARCHAR(100) NOT NULL,
        fecha_creacion DATETIME NOT NULL,
        red_social VARCHAR(50) NOT NULL,
        estado_moderacion ENUM('Pendiente', 'Aprobado', 'Malo') DEFAULT 'Pendiente',
        categoria_tendencia VARCHAR(100) DEFAULT NULL,
        justificacion_moderacion TEXT DEFAULT NULL,
        fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS historial_moderacion (
        id INT AUTO_INCREMENT PRIMARY KEY,
        post_id INT NOT NULL,
        usuario_id INT DEFAULT NULL,
        clasificacion ENUM('Aprobado', 'Malo') NOT NULL,
        categoria_tendencia VARCHAR(100) NOT NULL,
        justificacion TEXT NOT NULL,
        fecha_moderacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_historial_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        CONSTRAINT fk_historial_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS tendencias_dia (
        id INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(150) NOT NULL,
        resumen TEXT NOT NULL,
        enfoque_comercial TEXT NOT NULL,
        palabras_clave VARCHAR(255) NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
]

DATOS_SEMILLA = [
    """
    INSERT INTO usuarios (nombre, email, rol) VALUES
    ('Emilio PO', 'emilio.po@empresa.com', 'Product Owner'),
    ('Sandy SM', 'sandy.sm@empresa.com', 'Scrum Master'),
    ('Developer Team', 'dev@empresa.com', 'Developer')
    ON DUPLICATE KEY UPDATE nombre=nombre;
    """,
    """
    INSERT INTO productos (nombre, descripcion, sector) VALUES
    ('Análisis de Tendencias', 'Seguimiento de temas populares y moderación de contenido para ideas de publicaciones', 'Tecnología/Marketing')
    ON DUPLICATE KEY UPDATE nombre=nombre;
    """,
]


async def inicializar_esquema_si_no_existe() -> None:
    """
    Verifica y crea automáticamente las tablas del esquema y los datos iniciales
    si no existen al arrancar la aplicación (ideal para despliegues en Railway / Docker).
    """
    global _pool
    if _pool is None:
        return

    async with _pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for sql in TABLAS_DDL:
                await cursor.execute(sql.strip())
            for sql in DATOS_SEMILLA:
                try:
                    await cursor.execute(sql.strip())
                except Exception:
                    pass
        await conn.commit()
