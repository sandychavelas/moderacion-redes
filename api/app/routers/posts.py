from fastapi import APIRouter, Query, HTTPException, status
from app.services.social_media import SocialMediaConnector
import logging

logger = logging.getLogger("app")

router = APIRouter(
    prefix="/posts",
    tags=["Posts Extracción"],
)

connector = SocialMediaConnector()


@router.get("/fetch", response_model=list[dict], status_code=status.HTTP_200_OK)
async def fetch_posts(
    limit: int = Query(default=5, ge=1, le=20, description="Número de posts a obtener")
):
    """
    Obtiene posts de tendencia de la red social configurada (Reddit).
    En caso de desconexión o límites, devuelve datos realistas simulados para el desarrollo.
    """
    try:
        posts = await connector.obtener_posts_tendencia(limit=limit)
        return posts
    except Exception as e:
        logger.error(f"Error en endpoint /fetch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener posts de la red social: {str(e)}"
        )
