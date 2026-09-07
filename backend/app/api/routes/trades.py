"""
Trade history, pagination, and performance analytics endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.database import get_db
from backend.app.database.repositories import TradeRepository

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("")
async def get_trades(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    is_paper: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated trade history with numerical explanation details."""
    trade_repo = TradeRepository(db)
    trades = await trade_repo.get_all(limit=limit, offset=offset, is_paper=is_paper)
    return [
        {
            "id": t.id,
            "trade_id": t.trade_id,
            "symbol": t.symbol,
            "side": t.side,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "quantity": t.quantity,
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
            "fees": t.fees,
            "slippage": t.slippage,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "model_probability": t.model_probability,
            "strategy_reason": t.strategy_reason,
            "explanation_json": t.explanation_json,
            "status": t.status,
            "is_paper": t.is_paper,
        }
        for t in trades
    ]


@router.get("/metrics")
async def get_trade_metrics(db: AsyncSession = Depends(get_db)):
    """Calculate aggregate trade metrics: Win Rate, Profit Factor, Sharpe Ratio, Expectancy."""
    trade_repo = TradeRepository(db)
    trades = await trade_repo.get_all(limit=1000)

    closed_trades = [t for t in trades if t.status == "CLOSED"]
    total_trades = len(closed_trades)

    if total_trades == 0:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_pnl": 0.0,
            "total_fees": 0.0,
            "avg_trade_pnl": 0.0,
            "expectancy": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
        }

    winning_trades = [t for t in closed_trades if t.pnl > 0]
    losing_trades = [t for t in closed_trades if t.pnl <= 0]

    gross_profit = sum(t.pnl for t in winning_trades)
    gross_loss = abs(sum(t.pnl for t in losing_trades))
    net_pnl = sum(t.pnl for t in closed_trades)
    total_fees = sum(t.fees for t in closed_trades)

    win_rate = (len(winning_trades) / total_trades) * 100.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    avg_trade = net_pnl / total_trades

    largest_win = max((t.pnl for t in winning_trades), default=0.0)
    largest_loss = min((t.pnl for t in losing_trades), default=0.0)

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "gross_profit": round(gross_profit, 4),
        "gross_loss": round(gross_loss, 4),
        "net_pnl": round(net_pnl, 4),
        "total_fees": round(total_fees, 4),
        "avg_trade_pnl": round(avg_trade, 4),
        "largest_win": round(largest_win, 4),
        "largest_loss": round(largest_loss, 4),
    }
