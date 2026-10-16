from app.core.logging_config import setup_logging
setup_logging()
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from app.core.excepciones import ServerException, BDException
from app.core.validaciones import validar_configuracion_servidor
from app.dependencies.database import (
    crear_pool_conexiones,
    cerrar_pool_conexiones,
    inicializar_esquema_si_no_existe,
)
import asyncio
import logging

logger = logging.getLogger("app")
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.settings import settings
from slowapi.middleware import SlowAPIASGIMiddleware
from app.handlers.handlers import register_exception_handlers
from app.handlers.rate_limit_exceeded_handler import limiter
from fastapi.middleware.cors import CORSMiddleware
from app.routers.posts import router as posts_router
from app.routers.moderation import router as moderation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        validar_configuracion_servidor()
        
        # Conexión resiliente con reintentos para entornos cloud (Railway / Docker)
        max_reintentos = 8
        espera = 2
        for intento in range(1, max_reintentos + 1):
            try:
                await crear_pool_conexiones()
                logger.info("Conexión a MariaDB establecida exitosamente.")
                break
            except BDException as e:
                if intento == max_reintentos:
                    logger.error(f"Fallo definitivo al conectar a la BD: {e.descripcion_interna}")
                    raise
                logger.warning(
                    f"[Intento {intento}/{max_reintentos}] Esperando a la base de datos ({e.descripcion_interna}). Reintentando en {espera}s..."
                )
                await asyncio.sleep(espera)

        # Crear esquema y datos semilla si no existen
        await inicializar_esquema_si_no_existe()
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

    @app.get("/", tags=["Health"])
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "env": settings.ENV,
            "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DOCS_ENABLED else "disabled",
        }

    return app


def configure_cors(app: FastAPI) -> None:
    """
    Configura CORS con soporte para Railway y orígenes definidos.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https://.*\.railway\.app$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def include_routers(app: FastAPI) -> None:
    """Incluye todos los routers de la app bajo `API_V1_PREFIX`."""
    app.include_router(posts_router, prefix=settings.API_V1_PREFIX)
    app.include_router(moderation_router, prefix=settings.API_V1_PREFIX)


app = create_app()
