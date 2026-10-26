"""
HotWAY WebGIS Monolith Application Entrypoint & Factory
Author: Backend & WebGIS Engineer
Target: FastAPI Monolith with PostGIS, Redis & RL Inference
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.api.router import api_router
from backend.app.api import route_optimization

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("hotway.backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application Lifespan Event Manager.
    Handles startup initialization and graceful shutdown cleanup.
    """
    logger.info("Initializing HotWAY Backend Services...")
    logger.info("Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)

    # 1. Initialize DB Engine & verify connectivity
    try:
        from backend.app.core.database import engine
        async with engine.connect() as conn:
            logger.info("Database connection pool established successfully.")
    except Exception as exc:
        logger.warning(
            "Database connectivity check deferred or failed (running in offline/mock mode): %s",
            exc,
        )

    # 2. Initialize Redis connection pool
    try:
        from backend.app.services.telemetry_service import init_redis_pool
        await init_redis_pool()
        logger.info("Redis telemetry connection pool initialized.")
    except Exception as exc:
        logger.warning(
            "Redis connectivity deferred or failed (telemetry cache using in-memory fallback): %s",
            exc,
        )

    # 3. Singleton RL Model Loading with Safe Dijkstra Fallback
    app.state.rl_model_loaded = False
    app.state.policy_runner = None
    try:
        from pathlib import Path
        model_path = Path(settings.RL_MODEL_PATH)
        graph_path = Path(settings.OSM_GRAPH_PATH)

        if model_path.exists() and graph_path.exists():
            logger.info("Loading RL Model from %s...", model_path)
            from backend.app.services.rl_inference_service import HotWAYPolicyRunner
            app.state.policy_runner = HotWAYPolicyRunner(
                model_path=str(model_path),
                graph_path=str(graph_path)
            )
            app.state.rl_model_loaded = True
            logger.info("RL MaskablePPO Model loaded successfully as singleton.")
        else:
            logger.info(
                "RL Model (%s) or Graph (%s) not found on disk. "
                "Operating in SAFE DIJKSTRA FALLBACK mode (USE_DIJKSTRA_FALLBACK=True).",
                model_path,
                graph_path,
            )
    except Exception as exc:
        logger.error(
            "Failed to load RL model weights. Activating Dijkstra fallback. Error: %s",
            exc,
            exc_info=True,
        )
        app.state.rl_model_loaded = False
        app.state.policy_runner = None

    logger.info("HotWAY Backend is READY to serve requests.")
    yield

    # Shutdown Phase
    logger.info("Shutting down HotWAY Backend Services...")

    # Close Redis connection
    try:
        from backend.app.services.telemetry_service import close_redis_pool
        await close_redis_pool()
        logger.info("Redis connection pool closed.")
    except Exception as exc:
        logger.warning("Error closing Redis pool: %s", exc)

    # Dispose Database engine
    try:
        from backend.app.core.database import engine
        await engine.dispose()
        logger.info("Database connection engine disposed.")
    except Exception as exc:
        logger.warning("Error disposing database engine: %s", exc)

    # Disconnect active WebSockets
    try:
        from backend.app.services.ws_manager import ws_manager
        await ws_manager.disconnect_all()
        logger.info("All active WebSocket connections closed.")
    except Exception as exc:
        logger.warning("Error disconnecting WebSockets: %s", exc)

    logger.info("HotWAY Backend shutdown complete.")


def create_app() -> FastAPI:
    """
    Application Factory for HotWAY FastAPI Backend Monolith.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Intelligent food delivery dispatch & routing platform powered by Reinforcement Learning "
            "optimizing dynamic VRP with Newton's cooling law constraints on OpenStreetMap data of Hàng Gòn."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health Check Endpoints
    @application.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
    @application.get(f"{settings.API_V1_STR}/health", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_check():
        """
        Liveness and operational health probe.
        Returns system status, service modes, and version information.
        """
        return {
            "status": "healthy",
            "app_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "rl_model_loaded": getattr(application.state, "rl_model_loaded", False),
            "fallback_routing": settings.USE_DIJKSTRA_FALLBACK,
            "depot": {
                "name": settings.DEPOT_NAME,
                "lat": settings.DEPOT_LATITUDE,
                "lon": settings.DEPOT_LONGITUDE,
            },
        }

    # Root Metadata Endpoint
    @application.get("/", tags=["Root"])
    async def root():
        """
        Root landing endpoint directing clients to documentation and OpenAPI specification.
        """
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs_url": "/docs",
            "openapi_url": f"{settings.API_V1_STR}/openapi.json",
            "health_url": "/health",
        }

    # Include Main Modular API Router (supports both /api and /api/v1)
    application.include_router(api_router, prefix=settings.API_V1_STR)
    if settings.API_V1_STR != "/api/v1":
        application.include_router(api_router, prefix="/api/v1")

    # Include OptimoRoute-style CVRP Dispatching API (/api/v1/scenarios, /api/v1/plans, /api/v1/strategies/benchmark, /api/v1/sim)
    # Include HotWAY v7.0.0 Route Optimization & Real-Time Simulation API
    application.include_router(route_optimization.router, prefix="/api/v1")

    return application


# Global ASGI application instance for Uvicorn
app = create_app()
