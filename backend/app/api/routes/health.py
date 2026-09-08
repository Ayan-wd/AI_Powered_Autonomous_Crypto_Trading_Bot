"""
Health check endpoints for system uptime, database connectivity, and environment status.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.database.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive system health check."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": settings.TRADING_MODE.value,
        "trading_enabled": settings.TRADING_ENABLED,
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ping", status_code=status.HTTP_200_OK)
async def keep_alive_ping():
    """Lightweight keep-alive ping for uptime monitors to prevent free cloud spin-downs."""
    return {
        "status": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": settings.TRADING_MODE.value,
    }
