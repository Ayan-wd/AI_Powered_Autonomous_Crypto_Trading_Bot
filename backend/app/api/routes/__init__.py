"""API routes package."""
from fastapi import APIRouter
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.status import router as status_router
from backend.app.api.routes.account import router as account_router
from backend.app.api.routes.trades import router as trades_router
from backend.app.api.routes.config_routes import router as config_router
from backend.app.api.routes.market import router as market_router
from backend.app.api.routes.features_routes import router as features_router
from backend.app.api.routes.ml_routes import router as ml_router
from backend.app.api.routes.backtest_routes import router as backtest_router
from backend.app.api.routes.risk_routes import router as risk_router
from backend.app.api.routes.strategy_routes import router as strategy_router
from backend.app.api.routes.trading_routes import router as trading_router
from backend.app.api.routes.testnet_routes import router as testnet_router
from backend.app.api.routes.analytics_routes import router as analytics_router
from backend.app.api.websocket.ws_routes import router as ws_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(status_router)
api_router.include_router(account_router)
api_router.include_router(trades_router)
api_router.include_router(config_router)
api_router.include_router(market_router)
api_router.include_router(features_router)
api_router.include_router(ml_router)
api_router.include_router(backtest_router)
api_router.include_router(risk_router)
api_router.include_router(strategy_router)
api_router.include_router(trading_router)
api_router.include_router(testnet_router)
api_router.include_router(analytics_router)
api_router.include_router(ws_router)

__all__ = ["api_router"]
