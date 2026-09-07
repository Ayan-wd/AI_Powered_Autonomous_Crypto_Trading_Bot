"""
Trading and Bot Execution Control API Routes.
Provides interactive controls to start/stop the autonomous bot, inspect active positions,
manually close trades, and reset paper trading account.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.database.database import get_db
from backend.app.execution.order_manager import order_manager
from backend.app.execution.trading_bot import bot_engine

router = APIRouter(prefix="/trading", tags=["Trading Execution & Bot Daemon"])


@router.get("/bot/status")
async def get_bot_status():
    """Get the live status of the autonomous trading daemon and open positions."""
    return bot_engine.get_status()


@router.post("/bot/start")
async def start_bot(
    symbol: Optional[str] = Query(default="BTCUSDT"),
    timeframe: Optional[str] = Query(default="15m"),
):
    """Start the autonomous background trading loop."""
    bot_engine.symbol = symbol.upper()
    bot_engine.timeframe = timeframe
    res = await bot_engine.start()
    return res


@router.post("/bot/stop")
async def stop_bot():
    """Stop the autonomous background trading loop."""
    res = await bot_engine.stop()
    return res


@router.get("/position")
async def get_active_position():
    """Get the currently open active trading position, if any."""
    pos = order_manager.get_active_position()
    return {"active_position": pos, "has_open_position": pos is not None}


@router.post("/position/close")
async def close_position_manually(
    reason: str = Query(default="MANUAL_CLOSE"),
    db: AsyncSession = Depends(get_db),
):
    """Manually close the currently active position at live market price."""
    pos = order_manager.get_active_position()
    if not pos:
        raise HTTPException(status_code=400, detail="No active position currently open to close.")

    ticker = await bot_engine.market_engine.get_live_ticker(pos["symbol"])
    closed_summary = await order_manager.close_position(
        exit_price=ticker.price,
        exit_reason=reason,
        session=db,
    )
    return {
        "status": "SUCCESS",
        "message": f"Position on {pos['symbol']} closed manually at ${ticker.price:.2f}.",
        "trade": closed_summary,
    }


@router.post("/paper/reset")
async def reset_paper_trading(
    starting_capital: Optional[float] = Query(default=None),
):
    """Reset the paper trading account to pristine $50.00 baseline."""
    cap = starting_capital or settings.STARTING_CAPITAL
    order_manager.reset_paper_account(cap)
    return {
        "status": "SUCCESS",
        "message": f"Paper trading wallet and risk metrics reset to ${cap:.2f} USD.",
        "balances": order_manager.get_account_balances(),
    }
