from app.core.logging_config import setup_logging
setup_logging()
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from app.core.excepciones import ServerException, BDException
from app.core.validaciones import validar_configuracion_servidor
from app.dependencies.database import crear_pool_conexiones, cerrar_pool_conexiones
import logging

logger = logging.getLogger("app")
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.settings import settings
from slowapi.middleware import SlowAPIASGIMiddleware
from app.handlers.handlers import register_exception_handlers
from app.handlers.rate_limit_exceeded_handler import limiter
from fastapi.middleware.cors import CORSMiddleware
from app.routers.moderation import router as moderation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        validar_configuracion_servidor()
        await crear_pool_conexiones()
    except ServerException as e:
        logger.error(f"Error de configuración del servidor: {e.descripcion_interna or e.message}")
        import os
        os._exit(1)
    except BDException as e:
        logger.error(f"{e.descripcion_interna or e.message}")
        import os
        os._exit(1)
    yield
    await cerrar_pool_conexiones()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        docs_url="/docs" if settings.DOCS_ENABLED else None,
        redoc_url="/redoc" if settings.DOCS_ENABLED else None,
        openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    register_exception_handlers(app)
    app.add_middleware(SlowAPIASGIMiddleware)
    configure_cors(app)
    include_routers(app)
    return app


def configure_cors(app: FastAPI) -> None:
    """
    Configura CORS con `allow_credentials=True`.

    `allow_origins=*` está prohibido cuando `allow_credentials=True` (validado
    al arranque). Los headers permitidos incluyen `X-CSRF-Token` para el
    flujo CSRF y `X-Sensitive-Token` reservado para futuros endpoints
    sensibles.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type"
        ],
    )


def include_routers(app: FastAPI) -> None:
    """Incluye todos los routers de la app bajo `API_V1_PREFIX`."""
    app.include_router(moderation_router, prefix=settings.API_V1_PREFIX)


app = create_app()
