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


async def obtener_metricas_analisis(conexion: asyncmy.Connection) -> dict:
    """
    Retorna métricas agregadas sobre posts y tendencias para el Dashboard.
    """
    metricas = {
        "total_posts": 0,
        "por_estado": {"Pendiente": 0, "Aprobado": 0, "Malo": 0},
        "por_red_social": {},
        "top_tendencias": []
    }
    try:
        async with conexion.cursor() as cursor:
            # 1. Total posts
            await cursor.execute("SELECT COUNT(*) FROM posts")
            res_total = await cursor.fetchone()
            metricas["total_posts"] = res_total[0] if res_total else 0
            
            # 2. Por estado
            await cursor.execute("SELECT estado_moderacion, COUNT(*) FROM posts GROUP BY estado_moderacion")
            res_estados = await cursor.fetchall()
            for estado, count in res_estados:
                metricas["por_estado"][estado] = count
                
            # 3. Por red social
            await cursor.execute("SELECT red_social, COUNT(*) FROM posts GROUP BY red_social")
            res_redes = await cursor.fetchall()
            for red, count in res_redes:
                metricas["por_red_social"][red] = count

            # 4. Top tendencias
            await cursor.execute("""
                SELECT categoria_tendencia, COUNT(*) as cantidad 
                FROM posts 
                WHERE estado_moderacion = 'Aprobado' AND categoria_tendencia IS NOT NULL 
                GROUP BY categoria_tendencia 
                ORDER BY cantidad DESC 
                LIMIT 5
            """)
            res_tendencias = await cursor.fetchall()
            metricas["top_tendencias"] = [
                {"categoria": cat, "cantidad": cant} for cat, cant in res_tendencias
            ]
            
            return metricas
    except Exception as e:
        logger.error(f"Error al obtener métricas de análisis: {str(e)}")
        raise e


async def obtener_posts_pendientes(conexion: asyncmy.Connection, limit: int = 50) -> list[dict]:
    """
    Retorna la lista de posts en estado 'Pendiente' listos para moderarse.
    """
    sql = """
        SELECT id, id_externo, texto, autor, fecha_creacion, red_social, estado_moderacion 
        FROM posts 
        WHERE estado_moderacion = 'Pendiente' 
        ORDER BY fecha_creacion DESC 
        LIMIT %s
    """
    try:
        async with conexion.cursor(cursor=asyncmy.cursors.DictCursor) as cursor:
            await cursor.execute(sql, [limit])
            resultados = await cursor.fetchall()
            for r in resultados:
                if isinstance(r.get("fecha_creacion"), datetime):
                    r["fecha_creacion"] = r["fecha_creacion"].isoformat() + "Z"
            return resultados
    except Exception as e:
        logger.error(f"Error al obtener posts pendientes: {str(e)}")
        raise e


async def guardar_tendencia_dia(
    conexion: asyncmy.Connection,
    titulo: str,
    resumen: str,
    enfoque_comercial: str,
    palabras_clave: list[str]
) -> int:
    """
    Guarda un resumen de tendencia en la tabla tendencias_dia.
    """
    sql = """
        INSERT INTO tendencias_dia (titulo, resumen, enfoque_comercial, palabras_clave)
        VALUES (%s, %s, %s, %s)
    """
    palabras_clave_str = ",".join(palabras_clave)
    try:
        async with conexion.cursor() as cursor:
            await cursor.execute(sql, [titulo, resumen, enfoque_comercial, palabras_clave_str])
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error al guardar tendencia del día: {str(e)}")
        raise e


async def obtener_tendencias_dia(conexion: asyncmy.Connection, limit: int = 10) -> list[dict]:
    """
    Obtiene los resúmenes de tendencias del día guardados históricamente.
    """
    sql = "SELECT id, titulo, resumen, enfoque_comercial, palabras_clave, fecha_registro FROM tendencias_dia ORDER BY fecha_registro DESC LIMIT %s"
    try:
        async with conexion.cursor(cursor=asyncmy.cursors.DictCursor) as cursor:
            await cursor.execute(sql, [limit])
            resultados = await cursor.fetchall()
            for r in resultados:
                if isinstance(r.get("fecha_registro"), datetime):
                    r["fecha_registro"] = r["fecha_registro"].isoformat() + "Z"
                # Volver a parsear las palabras clave a lista
                if r.get("palabras_clave"):
                    r["palabras_clave"] = [p.strip() for p in r["palabras_clave"].split(",") if p.strip()]
                else:
                    r["palabras_clave"] = []
            return resultados
    except Exception as e:
        logger.error(f"Error al obtener tendencias históricas: {str(e)}")
        raise e

