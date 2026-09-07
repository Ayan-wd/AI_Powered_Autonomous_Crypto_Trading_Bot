"""
Security utilities and guards for the trading system.
Provides key masking, payload sanitization, environment safety audits, and emergency shutdown flags.
"""

from typing import Any, Dict, Optional
import re


def mask_api_key(key: Optional[str]) -> str:
    """Safely mask an API key for display."""
    if not key:
        return "NOT_CONFIGURED"
    if len(key) <= 8:
        return "***MASKED***"
    return f"{key[:4]}...{key[-4:]}"


def mask_secret(secret: Optional[str]) -> str:
    """Completely mask an API secret or password."""
    if not secret:
        return "NOT_CONFIGURED"
    return "************************"


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize sensitive key/secret fields from a dictionary."""
    sensitive_patterns = re.compile(r"(key|secret|password|token|auth|credential)", re.IGNORECASE)
    sanitized = {}

    for k, v in data.items():
        if sensitive_patterns.search(k):
            if isinstance(v, str):
                sanitized[k] = mask_api_key(v) if "key" in k.lower() else mask_secret(v)
            else:
                sanitized[k] = "***MASKED***"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        else:
            sanitized[k] = v

    return sanitized


def is_live_trading_allowed(trading_mode: str, live_trading_flag: bool, trading_enabled_flag: bool) -> bool:
    """Deterministic check if real-money trades are permitted."""
    return trading_mode == "LIVE" and live_trading_flag is True and trading_enabled_flag is True
