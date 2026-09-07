"""
Binance Testnet Execution and Account API Routes.
Provides status verification, live account balance queries, order tracking, and safety audits.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.execution.binance_client import BinanceClient

router = APIRouter(prefix="/testnet", tags=["Binance Testnet Execution"])
testnet_client = BinanceClient(testnet=True)


@router.get("/status")
async def get_testnet_status():
    """Verify Binance Spot Testnet connectivity, latency, and operational health."""
    sys_status = await testnet_client.get_system_status()
    sys_status["api_key_configured"] = bool(settings.BINANCE_API_KEY)
    sys_status["trading_mode"] = settings.TRADING_MODE
    sys_status["trading_enabled"] = settings.TRADING_ENABLED
    sys_status["live_trading_safety_flag"] = settings.LIVE_TRADING
    return sys_status


@router.get("/account")
async def get_testnet_account():
    """
    Fetch live Binance Testnet account permissions and asset balances.
    Verifies that withdrawal permissions are disabled (security audit constraint).
    """
    if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
        return {
            "status": "UNCONFIGURED",
            "message": "Binance API Key and Secret are not configured in environment.",
            "can_trade": False,
            "can_withdraw": False,
            "balances": {"USDT": 50.0, "BTC": 0.0},
        }

    try:
        acc_info = await testnet_client.get_account_info()
        # Security sanity check: Bot API keys must NOT have withdrawal permissions
        acc_info["security_audit_passed"] = not acc_info.get("can_withdraw", False)
        return {
            "status": "CONNECTED",
            "account": acc_info,
        }
    except Exception as e:
        logger.error(f"Error querying Binance Testnet account: {e}")
        return {
            "status": "ERROR",
            "message": str(e),
            "can_trade": False,
            "can_withdraw": False,
            "balances": {},
        }


@router.get("/open-orders")
async def get_testnet_open_orders(
    symbol: Optional[str] = Query(default=None),
):
    """Fetch active open orders on Binance Spot Testnet."""
    if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
        return {"open_orders": [], "count": 0, "status": "DEMO_MODE"}

    try:
        orders = await testnet_client.get_open_orders(symbol=symbol)
        return {"open_orders": orders, "count": len(orders), "status": "CONNECTED"}
    except Exception as e:
        logger.error(f"Error querying Binance Testnet open orders: {e}")
        return {"open_orders": [], "count": 0, "status": "ERROR", "error": str(e)}
