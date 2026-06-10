import logging
from datetime import datetime
import asyncmy
import asyncmy.cursors

logger = logging.getLogger("app")


async def guardar_posts(conexion: asyncmy.Connection, posts: list[dict]) -> int:
    """
    Inserta una lista de posts en la base de datos de forma asíncrona.
    Utiliza INSERT IGNORE para evitar duplicación basada en la restricción UNIQUE del campo id_externo.
    Devuelve la cantidad de registros nuevos insertados con éxito.
    """
    if not posts:
        return 0

    sql = """
        INSERT IGNORE INTO posts 
        (id_externo, texto, autor, fecha_creacion, red_social, estado_moderacion, categoria_tendencia, justificacion_moderacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    registros_insertados = 0
    try:
        async with conexion.cursor() as cursor:
            # Preparar los parámetros para ejecución por lotes (executemany)
            parametros = []
            for post in posts:
                # Normalizar fechas para MySQL
                fecha_creacion_raw = post.get("fecha_creacion")
                if isinstance(fecha_creacion_raw, str):
                    try:
                        # Remover la Z de zona horaria si existe y parsear
                        fecha_str = fecha_creacion_raw.replace("Z", "")
                        fecha_creacion = datetime.fromisoformat(fecha_str)
                    except ValueError:
                        fecha_creacion = datetime.now()
                elif isinstance(fecha_creacion_raw, datetime):
                    fecha_creacion = fecha_creacion_raw
                else:
                    fecha_creacion = datetime.now()

                parametros.append((
                    post.get("id_externo"),
                    post.get("texto"),
                    post.get("autor"),
                    fecha_creacion,
                    post.get("red_social", "Reddit"),
                    post.get("estado_moderacion", "Pendiente"),
                    post.get("categoria_tendencia"),
                    post.get("justificacion_moderacion")
                ))

            await cursor.executemany(sql, parametros)
            registros_insertados = cursor.rowcount
            logger.info(f"Fueron insertados {registros_insertados} posts nuevos en la base de datos.")
            return registros_insertados
    except Exception as e:
        logger.error(f"Error al guardar posts en la base de datos: {str(e)}")
        raise e


async def obtener_posts(
    conexion: asyncmy.Connection,
    keyword: str = None,
    estado: str = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    """
    Obtiene posts de la base de datos con soporte para filtros de búsqueda por palabra clave (MDREC-7),
    estado de moderación, orden cronológico descendente y paginación.
    """
    sql = "SELECT id, id_externo, texto, autor, fecha_creacion, red_social, estado_moderacion, categoria_tendencia, justificacion_moderacion, fecha_extraccion FROM posts WHERE 1=1"
    params = []

    if keyword and keyword.strip():
        sql += " AND texto LIKE %s"
        params.append(f"%{keyword.strip()}%")

    if estado and estado.strip():
        sql += " AND estado_moderacion = %s"
        params.append(estado.strip())

    sql += " ORDER BY fecha_creacion DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    try:
        async with conexion.cursor(cursor=asyncmy.cursors.DictCursor) as cursor:
            await cursor.execute(sql, params)
            resultados = await cursor.fetchall()
            
            # Formatear objetos datetime a strings ISO para el response JSON
            for r in resultados:
                if isinstance(r.get("fecha_creacion"), datetime):
                    r["fecha_creacion"] = r["fecha_creacion"].isoformat() + "Z"
                if isinstance(r.get("fecha_extraccion"), datetime):
                    r["fecha_extraccion"] = r["fecha_extraccion"].isoformat() + "Z"
                    
            return resultados
    except Exception as e:
        logger.error(f"Error al obtener posts de la base de datos: {str(e)}")
        raise e


async def obtener_post_por_id(conexion: asyncmy.Connection, post_id: int) -> dict | None:
    """
    Recupera un post específico de la base de datos por su ID primaria.
    """
    sql = "SELECT id, id_externo, texto, autor, fecha_creacion, red_social, estado_moderacion, categoria_tendencia, justificacion_moderacion, fecha_extraccion FROM posts WHERE id = %s"
    try:
        async with conexion.cursor(cursor=asyncmy.cursors.DictCursor) as cursor:
            await cursor.execute(sql, [post_id])
            resultado = await cursor.fetchone()
            if resultado:
                if isinstance(resultado.get("fecha_creacion"), datetime):
                    resultado["fecha_creacion"] = resultado["fecha_creacion"].isoformat() + "Z"
                if isinstance(resultado.get("fecha_extraccion"), datetime):
                    resultado["fecha_extraccion"] = resultado["fecha_extraccion"].isoformat() + "Z"
            return resultado
    except Exception as e:
        logger.error(f"Error al obtener post por id={post_id}: {str(e)}")
        raise e


async def actualizar_moderacion(
    conexion: asyncmy.Connection,
    post_id: int,
    estado: str,
    categoria: str,
    justificacion: str
) -> bool:
    """
    Actualiza el estado de moderación, la tendencia y la justificación de un post.
    """
    sql = """
        UPDATE posts 
        SET estado_moderacion = %s, 
            categoria_tendencia = %s, 
            justificacion_moderacion = %s 
        WHERE id = %s
    """
    try:
        async with conexion.cursor() as cursor:
            await cursor.execute(sql, [estado, categoria, justificacion, post_id])
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error al actualizar moderación de post id={post_id}: {str(e)}")
        raise e


async def guardar_historial_moderacion(
    conexion: asyncmy.Connection,
    post_id: int,
    clasificacion: str,
    categoria_tendencia: str,
    justificacion: str
) -> int:
    """
    Crea un registro de auditoría en la tabla historial_moderacion.
    """
    sql = """
        INSERT INTO historial_moderacion 
        (post_id, usuario_id, clasificacion, categoria_tendencia, justificacion) 
        VALUES (%s, NULL, %s, %s, %s)
    """
    try:
        async with conexion.cursor() as cursor:
            await cursor.execute(sql, [post_id, clasificacion, categoria_tendencia, justificacion])
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error al guardar historial de moderación para post id={post_id}: {str(e)}")
        raise e
