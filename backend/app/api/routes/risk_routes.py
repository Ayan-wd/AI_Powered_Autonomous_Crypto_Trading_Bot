"""
Risk Management API routes for inspecting circuit breakers, loss limits, and position sizing.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.database.database import get_db
from backend.app.database.repositories import EquityRepository
from backend.app.risk.risk_manager import risk_manager

router = APIRouter(prefix="/risk", tags=["Risk Management"])


@router.get("/status")
async def get_risk_status(db: AsyncSession = Depends(get_db)):
    """Retrieve live risk parameters, circuit breakers, and loss limits."""
    equity_repo = EquityRepository(db)
    latest_snapshot = await equity_repo.get_latest()
    current_equity = latest_snapshot.total_equity if latest_snapshot else settings.STARTING_CAPITAL

    snapshot = risk_manager.drawdown_controller.get_risk_snapshot(current_equity)
    snapshot["max_risk_per_trade_pct"] = settings.MAX_RISK_PER_TRADE_PCT * 100.0
    snapshot["max_position_size_usd"] = settings.MAX_POSITION_SIZE_USD
    snapshot["starting_capital"] = settings.STARTING_CAPITAL
    return snapshot


@router.post("/evaluate-sizing")
async def evaluate_sizing(
    price: float = Query(gt=0),
    stop_loss: Optional[float] = Query(default=None),
    atr: float = Query(default=0.0),
    equity: Optional[float] = Query(default=None),
):
    """Simulate position sizing calculation for a hypothetical price and stop loss."""
    current_equity = equity or settings.STARTING_CAPITAL
    eval_result = risk_manager.evaluate_order(
        account_equity=current_equity,
        current_price=price,
        side="BUY",
        stop_loss_price=stop_loss,
        atr=atr,
    )
    return eval_result
