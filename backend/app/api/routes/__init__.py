"""API routes package."""
from fastapi import APIRouter
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.status import router as status_router
from backend.app.api.routes.account import router as account_router
from backend.app.api.routes.trades import router as trades_router
from backend.app.api.routes.config_routes import router as config_router
from backend.app.api.routes.market import router as market_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(status_router)
api_router.include_router(account_router)
api_router.include_router(trades_router)
api_router.include_router(config_router)
api_router.include_router(market_router)

__all__ = ["api_router"]
