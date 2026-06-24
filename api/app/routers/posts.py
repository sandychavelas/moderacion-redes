import logging
import asyncio
from fastapi import APIRouter, Query, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.social_media import SocialMediaConnector
from app.services.ai_moderator import AIModeratorService
from app.dependencies.database import obtener_conexion_bd
from app.repository import posts_repo as repo
import asyncmy

logger = logging.getLogger("app")

router = APIRouter(
    prefix="/posts",
    tags=["Posts Moderación & Extracción"],
)

connector = SocialMediaConnector()
ai_moderator = AIModeratorService()


# --- ESQUEMAS DE PYDANTIC PARA PETICIONES Y RESPUESTAS ---

class PostResponse(BaseModel):
    id: int
    id_externo: str
    texto: str
    autor: str
    fecha_creacion: str
    red_social: str
    estado_moderacion: str
    categoria_tendencia: Optional[str] = None
    justificacion_moderacion: Optional[str] = None
    fecha_extraccion: str


class FetchAndStoreResponse(BaseModel):
    status: str
    extraidos: int
    nuevos_guardados: int


class ModerationResponse(BaseModel):
    post_id: int
    estado_moderacion: str
    categoria_tendencia: str
    justificacion: str
    historial_id: int


class TopTendencia(BaseModel):
    categoria: str
    cantidad: int


class AnalyticsResponse(BaseModel):
    total_posts: int
    por_estado: dict
    por_red_social: dict
    top_tendencias: List[TopTendencia]


class BatchModerationItem(BaseModel):
    post_id: int
    texto: str
    autor: str
    red_social: str
    estado_moderacion: str
    categoria_tendencia: str
    justificacion: str
    historial_id: int


class BatchModerationResponse(BaseModel):
    status: str
    procesados: int
    moderados: List[BatchModerationItem]


class TrendResponse(BaseModel):
    id: int
    titulo: str
    resumen: str
    enfoque_comercial: str
    palabras_clave: List[str]
    fecha_registro: Optional[str] = None


# --- ENDPOINTS ---

@router.get("/fetch", response_model=List[dict], status_code=status.HTTP_200_OK)
async def fetch_posts_raw(
    limit: int = Query(default=5, ge=1, le=20, description="Número de posts a obtener directamente de la red social")
):
    """
    Obtiene posts de tendencia de la red social (Reddit) de forma directa, sin guardarlos en la base de datos.
    Útil para previsualizar contenido en tiempo real.
    """
    try:
        posts = await connector.obtener_posts_tendencia(limit=limit)
        return posts
    except Exception as e:
        logger.error(f"Error en endpoint GET /fetch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener posts de la red social: {str(e)}"
        )


@router.post("/fetch-and-store", response_model=FetchAndStoreResponse, status_code=status.HTTP_201_CREATED)
async def fetch_and_store_posts(
    limit: int = Query(default=5, ge=1, le=20, description="Número de posts a extraer y guardar"),
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Extrae posts de tendencia de redes sociales y los guarda de forma automática en la base de datos.
    Evita guardar duplicados controlando el 'id_externo' único del post.
    """
    try:
        # 1. Extraer posts de la red social
        posts = await connector.obtener_posts_tendencia(limit=limit)
        
        # 2. Guardar en la base de datos (con control de duplicados mediante INSERT IGNORE)
        nuevos_insertados = await repo.guardar_posts(conexion, posts)
        
        return FetchAndStoreResponse(
            status="success",
            extraidos=len(posts),
            nuevos_guardados=nuevos_insertados
        )
    except Exception as e:
        logger.error(f"Error en endpoint POST /fetch-and-store: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar y almacenar posts: {str(e)}"
        )


@router.get("", response_model=List[PostResponse], status_code=status.HTTP_200_OK)
async def list_posts(
    keyword: Optional[str] = Query(default=None, description="Filtro de búsqueda por palabra clave (ej. comprar, venta, precio, etc.)"),
    estado: Optional[str] = Query(default=None, description="Filtro por estado de moderación (Pendiente, Aprobado, Malo)"),
    limit: int = Query(default=20, ge=1, le=100, description="Límite de registros para paginación"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación"),
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Obtiene la lista de posts almacenados en la base de datos.
    Permite filtrar dinámicamente por palabra clave (MDREC-7) y por estado de moderación (MDREC-8).
    """
    try:
        posts = await repo.obtener_posts(
            conexion=conexion,
            keyword=keyword,
            estado=estado,
            limit=limit,
            offset=offset
        )
        return posts
    except Exception as e:
        logger.error(f"Error en endpoint GET /posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar base de datos de posts: {str(e)}"
        )


@router.post("/{post_id}/moderate", response_model=ModerationResponse, status_code=status.HTTP_200_OK)
async def moderate_stored_post(
    post_id: int,
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Modera un post específico que ya está guardado en la base de datos.
    Llama a la IA DeepSeek para analizarlo, actualiza su clasificación, tendencia y justificación en la BD,
    y registra un log histórico en la tabla de historial_moderacion.
    """
    try:
        # 1. Recuperar el post de la BD
        post = await repo.obtener_post_por_id(conexion, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El post con ID {post_id} no fue encontrado en la base de datos."
            )

        # 2. Llama al moderador de IA DeepSeek
        analisis = await ai_moderator.moderar_post(texto=post["texto"])
        clasificacion = analisis.get("clasificacion", "Malo")
        categoria_tendencia = analisis.get("categoria_tendencia", "General")
        justificacion = analisis.get("justificacion", "Clasificación automática por IA.")

        # 3. Actualizar la tabla de posts con el veredicto
        await repo.actualizar_moderacion(
            conexion=conexion,
            post_id=post_id,
            estado=clasificacion,
            categoria=categoria_tendencia,
            justificacion=justificacion
        )

        # 4. Registrar la auditoría histórica en la tabla historial_moderacion
        historial_id = await repo.guardar_historial_moderacion(
            conexion=conexion,
            post_id=post_id,
            clasificacion=clasificacion,
            categoria_tendencia=categoria_tendencia,
            justificacion=justificacion
        )

        return ModerationResponse(
            post_id=post_id,
            estado_moderacion=clasificacion,
            categoria_tendencia=categoria_tendencia,
            justificacion=justificacion,
            historial_id=historial_id
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en endpoint POST /posts/{post_id}/moderate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el proceso de moderación del post: {str(e)}"
        )


@router.get("/analytics", response_model=AnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_analytics(
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Retorna métricas e indicadores estadísticos consolidados para el Dashboard.
    """
    try:
        metricas = await repo.obtener_metricas_analisis(conexion)
        return metricas
    except Exception as e:
        logger.error(f"Error en endpoint GET /posts/analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular métricas de análisis: {str(e)}"
        )


@router.post("/moderate-pending", response_model=BatchModerationResponse, status_code=status.HTTP_200_OK)
async def moderate_pending_posts(
    limit: int = Query(default=10, ge=1, le=50, description="Límite de posts a moderar en lote"),
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Identifica posts en estado 'Pendiente' y los modera de forma concurrente con DeepSeek.
    """
    try:
        # 1. Obtener posts pendientes
        pendientes = await repo.obtener_posts_pendientes(conexion, limit=limit)
        if not pendientes:
            return BatchModerationResponse(
                status="success",
                procesados=0,
                moderados=[]
            )

        # 2. Moderar concurrentemente
        tareas = [ai_moderator.moderar_post(post["texto"]) for post in pendientes]
        resultados_ia = await asyncio.gather(*tareas)

        # 3. Guardar cambios en BD e historial secuencialmente
        moderados = []
        for post, analisis in zip(pendientes, resultados_ia):
            post_id = post["id"]
            clasificacion = analisis.get("clasificacion", "Malo")
            categoria_tendencia = analisis.get("categoria_tendencia", "General")
            justificacion = analisis.get("justificacion", "Clasificación automática por IA en lote.")

            # Actualizar post en BD
            await repo.actualizar_moderacion(
                conexion=conexion,
                post_id=post_id,
                estado=clasificacion,
                categoria=categoria_tendencia,
                justificacion=justificacion
            )

            # Registrar en historial
            historial_id = await repo.guardar_historial_moderacion(
                conexion=conexion,
                post_id=post_id,
                clasificacion=clasificacion,
                categoria_tendencia=categoria_tendencia,
                justificacion=justificacion
            )

            moderados.append(
                BatchModerationItem(
                    post_id=post_id,
                    texto=post["texto"],
                    autor=post["autor"],
                    red_social=post["red_social"],
                    estado_moderacion=clasificacion,
                    categoria_tendencia=categoria_tendencia,
                    justificacion=justificacion,
                    historial_id=historial_id
                )
            )

        return BatchModerationResponse(
            status="success",
            procesados=len(pendientes),
            moderados=moderados
        )
    except Exception as e:
        logger.error(f"Error en endpoint POST /posts/moderate-pending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el proceso de moderación en lote: {str(e)}"
        )


@router.post("/generate-trends", response_model=List[TrendResponse], status_code=status.HTTP_201_CREATED)
async def generate_daily_trends(
    limit: int = Query(default=30, ge=1, le=100, description="Cantidad máxima de posts aprobados a analizar"),
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Agrupa posts con estado 'Aprobado', analiza sus textos con DeepSeek,
    y sintetiza las principales tendencias guardándolas en 'tendencias_dia'.
    """
    try:
        # 1. Obtener posts aprobados
        posts_aprobados = await repo.obtener_posts(conexion, estado="Aprobado", limit=limit)
        textos = [p["texto"] for p in posts_aprobados if p.get("texto")]

        if not textos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay posts aprobados suficientes en la base de datos para sintetizar tendencias."
            )

        # 2. Generar tendencias con IA
        tendencias_ia = await ai_moderator.sintetizar_tendencias_del_dia(textos)

        # 3. Guardar e insertar cada tendencia en BD
        guardadas = []
        for t in tendencias_ia:
            titulo = t.get("titulo", "Tendencia sin título")
            resumen = t.get("resumen", "")
            enfoque_comercial = t.get("enfoque_comercial", "")
            palabras_clave = t.get("palabras_clave", [])

            tendencia_id = await repo.guardar_tendencia_dia(
                conexion=conexion,
                titulo=titulo,
                resumen=resumen,
                enfoque_comercial=enfoque_comercial,
                palabras_clave=palabras_clave
            )

            guardadas.append(
                TrendResponse(
                    id=tendencia_id,
                    titulo=titulo,
                    resumen=resumen,
                    enfoque_comercial=enfoque_comercial,
                    palabras_clave=palabras_clave
                )
            )

        return guardadas
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en endpoint POST /posts/generate-trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar y guardar tendencias del día: {str(e)}"
        )


@router.get("/trends", response_model=List[TrendResponse], status_code=status.HTTP_200_OK)
async def list_trends(
    limit: int = Query(default=10, ge=1, le=50, description="Límite de tendencias a listar"),
    conexion: asyncmy.Connection = Depends(obtener_conexion_bd)
):
    """
    Obtiene los resúmenes de tendencias del día guardados históricamente.
    """
    try:
        trends = await repo.obtener_tendencias_dia(conexion, limit=limit)
        return trends
    except Exception as e:
        logger.error(f"Error en endpoint GET /posts/trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar tendencias históricas: {str(e)}"
        )
