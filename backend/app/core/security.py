"""
Security utilities and guards for the trading system.
Provides key masking, payload validation, and emergency shutdown flags.
"""

from typing import Optional


def mask_api_key(key: Optional[str]) -> str:
    """Safely mask an API key for display."""
    if not key:
        return "NOT_CONFIGURED"
    if len(key) <= 8:
        return "***MASKED***"
    return f"{key[:4]}...{key[-4:]}"


def is_live_trading_allowed(trading_mode: str, live_trading_flag: bool, trading_enabled_flag: bool) -> bool:
    """Deterministic check if real-money trades are permitted."""
    return trading_mode == "LIVE" and live_trading_flag is True and trading_enabled_flag is True
