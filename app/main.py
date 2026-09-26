from __future__ import annotations

"""J.A.R.V.I.S. Mark V - Main Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.system_service import SystemService

setup_logging()
logger = logging.getLogger("JARVIS_CORE")
FRONTEND_DIR = Path("frontend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle events, enforcing fail-fast validation on startup.

    Args:
        app: FastAPI application instance.

    Yields:
        None
    """
    logger.info("Initializing J.A.R.V.I.S. Mark V Core services...")
    # Execução obrigatória de rotinas de hardening e validações iniciais (Fail-Fast)
    try:
        settings.validate_fail_fast()
        logger.info("Security hardening and environment validation passed.")
    except Exception as exc:
        logger.critical("STARTUP HARDENING FAILED: %s", exc)
        raise

    logger.info("J.A.R.V.I.S. Mark V online and ready on %s:%d.", settings.host, settings.port)
    yield
    logger.info("Shutting down J.A.R.V.I.S. Mark V services...")


def create_application() -> FastAPI:
    """Factory function initializing the configured FastAPI application.

    Returns:
        FastAPI: Configured web server instance.
    """
    app = FastAPI(
        title="J.A.R.V.I.S. Mark V Core API",
        description="Resilient, modular, AI-first decoupled service backend.",
        version="5.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static assets for HUD if directory is present
    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_hud_interface() -> FileResponse:
            """Serves the primary HUD HTML canvas."""
            return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/healthz", tags=["Health"])
    async def k8s_health_check() -> dict[str, object]:
        """Kubernetes and cloud-native healthz check endpoint."""
        return {"status": "ok", "service": "jarvis-core", "telemetry": SystemService.get_telemetry()}

    app.include_router(api_router)
    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
