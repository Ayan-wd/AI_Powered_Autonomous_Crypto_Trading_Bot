"""
Account balance, capital tracking, and equity snapshot endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.database.database import get_db
from backend.app.database.repositories import EquityRepository, TradeRepository

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("/summary")
async def get_account_summary(db: AsyncSession = Depends(get_db)):
    """Retrieve capital, equity, PnL, and performance summary."""
    equity_repo = EquityRepository(db)
    latest_snapshot = await equity_repo.get_latest()

    # Adapt equity baseline if starting capital was upgraded (e.g. from $50 to $10,000 testnet balance)
    if latest_snapshot and latest_snapshot.total_equity >= settings.STARTING_CAPITAL * 0.5:
        total_equity = latest_snapshot.total_equity
        available_balance = latest_snapshot.available_balance
        unrealized_pnl = latest_snapshot.unrealized_pnl
        realized_pnl = latest_snapshot.realized_pnl
        drawdown_pct = latest_snapshot.drawdown_pct
    else:
        total_equity = settings.STARTING_CAPITAL
        available_balance = settings.STARTING_CAPITAL
        unrealized_pnl = 0.0
        realized_pnl = 0.0
        drawdown_pct = 0.0

    net_profit = total_equity - settings.STARTING_CAPITAL
    return_pct = (net_profit / settings.STARTING_CAPITAL) * 100.0 if settings.STARTING_CAPITAL > 0 else 0.0

    return {
        "starting_capital": settings.STARTING_CAPITAL,
        "total_equity": total_equity,
        "available_balance": available_balance,
        "base_currency": settings.BASE_CURRENCY,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl,
        "net_profit": net_profit,
        "return_pct": return_pct,
        "drawdown_pct": drawdown_pct,
        "max_drawdown_limit_pct": settings.MAX_DRAWDOWN_PCT,
        "mode": settings.TRADING_MODE.value,
        "open_positions": [],
    }


@router.get("/equity-history")
async def get_equity_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Retrieve historical equity snapshots for equity curve charting."""
    equity_repo = EquityRepository(db)
    snapshots = await equity_repo.get_history(limit=limit)
    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "total_equity": s.total_equity,
            "available_balance": s.available_balance,
            "unrealized_pnl": s.unrealized_pnl,
            "realized_pnl": s.realized_pnl,
            "drawdown_pct": s.drawdown_pct,
        }
        for s in snapshots
    ]
