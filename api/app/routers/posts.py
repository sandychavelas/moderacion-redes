from fastapi import APIRouter, Query, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.social_media import SocialMediaConnector
from app.services.ai_moderator import AIModeratorService
from app.dependencies.database import obtener_conexion_bd
from app.repository import posts_repo as repo
import asyncmy
import logging

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

        # 2. Llamar al moderador de IA DeepSeek
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
