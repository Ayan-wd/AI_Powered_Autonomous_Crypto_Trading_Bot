"""
Bot operational state, kill switch, and active strategy status endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import BotState, settings

router = APIRouter(prefix="/status", tags=["Status"])

# In-memory runtime state for the bot engine
_runtime_state = {
    "state": BotState.RUNNING.value if settings.TRADING_ENABLED else BotState.STOPPED.value,
    "kill_switch_active": False,
    "current_symbol": settings.TRADING_SYMBOL,
    "current_timeframe": settings.DEFAULT_TIMEFRAME,
    "uptime_since": datetime.now(timezone.utc).isoformat(),
    "last_signal": "HOLD / NO TRADE",
    "last_signal_time": None,
    "daily_trades_count": 0,
    "daily_loss_usd": 0.0,
}


@router.get("")
async def get_bot_status():
    """Retrieve the current live state, mode, and risk flags of the bot."""
    return {
        "bot_state": _runtime_state["state"],
        "trading_mode": settings.TRADING_MODE.value,
        "trading_enabled": settings.TRADING_ENABLED,
        "live_trading_allowed": settings.LIVE_TRADING,
        "kill_switch_active": _runtime_state["kill_switch_active"],
        "symbol": _runtime_state["current_symbol"],
        "timeframe": _runtime_state["current_timeframe"],
        "uptime_since": _runtime_state["uptime_since"],
        "daily_trades_count": _runtime_state["daily_trades_count"],
        "max_daily_trades": settings.MAX_DAILY_TRADES,
        "daily_loss_usd": _runtime_state["daily_loss_usd"],
        "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT,
        "last_signal": _runtime_state["last_signal"],
        "last_signal_time": _runtime_state["last_signal_time"],
    }


@router.post("/kill-switch")
async def trigger_kill_switch():
    """Emergency shutdown kill switch: stops trading and freezes orders."""
    _runtime_state["kill_switch_active"] = True
    _runtime_state["state"] = BotState.EMERGENCY_STOP.value
    return {
        "status": "EMERGENCY_STOP_TRIGGERED",
        "message": "Kill switch activated. All automated trading is immediately halted.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/reset-kill-switch")
async def reset_kill_switch():
    """Reset emergency kill switch back to normal state."""
    _runtime_state["kill_switch_active"] = False
    _runtime_state["state"] = BotState.RUNNING.value if settings.TRADING_ENABLED else BotState.STOPPED.value
    return {
        "status": "KILL_SWITCH_RESET",
        "bot_state": _runtime_state["state"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
