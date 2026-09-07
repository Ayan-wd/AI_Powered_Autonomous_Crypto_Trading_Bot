"""
Performance and Quantitative Analytics API Routes.
Provides institutional performance metrics, Sharpe/Sortino ratios, holding periods, and equity curves.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.database.database import get_db
from backend.app.database.repositories import EquityRepository, TradeRepository
from backend.app.monitoring.performance_analytics import performance_engine

router = APIRouter(prefix="/analytics", tags=["Performance & Quantitative Analytics"])


@router.get("/performance")
async def get_performance_analytics(
    db: AsyncSession = Depends(get_db),
    is_paper: Optional[bool] = None,
):
    """
    Compute full institutional performance analytics including Win Rate, Expectancy,
    Profit Factor, Sharpe/Sortino ratios, Payoff ratio, and holding period distribution.
    """
    trade_repo = TradeRepository(db)
    equity_repo = EquityRepository(db)

    trades = await trade_repo.get_all(limit=500, is_paper=is_paper)
    snapshots = await equity_repo.get_history(limit=500)
    snapshots = list(reversed(snapshots))  # Chronological order

    trade_metrics = performance_engine.calculate_trade_metrics(
        trades=trades,
        starting_capital=settings.STARTING_CAPITAL,
    )
    equity_metrics = performance_engine.calculate_equity_metrics(
        snapshots=snapshots,
        starting_capital=settings.STARTING_CAPITAL,
    )

    return {
        "status": "SUCCESS",
        "starting_capital": settings.STARTING_CAPITAL,
        "trading_mode": settings.TRADING_MODE,
        "trade_performance": trade_metrics,
        "risk_adjusted_metrics": equity_metrics,
    }


@router.get("/equity-history")
async def get_equity_history(
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Fetch high-resolution timestamped equity history for charting."""
    equity_repo = EquityRepository(db)
    snapshots = await equity_repo.get_history(limit=limit)
    snapshots = list(reversed(snapshots))  # Chronological order

    return [
        {
            "id": s.id,
            "timestamp": s.timestamp.isoformat(),
            "total_equity": round(s.total_equity, 2),
            "available_balance": round(s.available_balance, 2),
            "unrealized_pnl": round(s.unrealized_pnl, 2),
            "realized_pnl": round(s.realized_pnl, 2),
            "drawdown_pct": round(s.drawdown_pct, 2),
            "high_water_mark": round(s.high_water_mark, 2),
            "open_positions_count": s.open_positions_count,
            "mode": s.mode,
        }
        for s in snapshots
    ]
