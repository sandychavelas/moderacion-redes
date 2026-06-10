from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.ai_moderator import AIModeratorService
import logging

logger = logging.getLogger("app")

router = APIRouter(
    prefix="/moderation",
    tags=["Moderación IA"],
)

service = AIModeratorService()


class ModerationRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto del post que se va a clasificar y moderar"
    )


class ModerationResponse(BaseModel):
    clasificacion: str = Field(..., description="Clasificación del post: 'Aprobado' o 'Malo'")
    categoria_tendencia: str = Field(..., description="Categoría o tendencia asignada al post")
    palabras_clave: list[str] = Field(..., description="Palabras clave extraídas del post")
    justificacion: str = Field(..., description="Justificación de la clasificación por la IA")


@router.post(
    "/classify",
    response_model=ModerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Clasificar post con IA",
    description="Analiza y clasifica un post como Aprobado o Malo usando DeepSeek IA, y extrae su tendencia."
)
async def classify_post(request: ModerationRequest):
    """
    Recibe el texto de un post, llama a DeepSeek para su clasificación y retorna la decisión.
    """
    try:
        resultado = await service.moderar_post(texto=request.texto)
        return resultado
    except Exception as e:
        logger.error(f"Error en endpoint /classify: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la moderación con IA: {str(e)}"
        )
