"""
Main FastAPI application entry point.
Configures lifespan events (DB initialization, logger setup, graceful shutdown),
CORS middleware, error handling, and API routing.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger, setup_logging
from backend.app.database.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for clean startup and shutdown."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} in {settings.TRADING_MODE.value} mode")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down trading application...")
    await close_db()


def create_app() -> FastAPI:
    """Factory function for FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Autonomous AI-Powered Cryptocurrency Trading System with strict quantitative risk management.",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "AI Autonomous Crypto Trading Engine API",
            "version": settings.VERSION,
            "mode": settings.TRADING_MODE.value,
            "trading_enabled": settings.TRADING_ENABLED,
            "docs": "/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
