"""
Unit tests for configuration loading, safety validation, and live trading safeguards.
"""

import pytest
from pydantic import ValidationError
from backend.app.core.config import Settings, TradingMode


def test_default_config_is_safe():
    """Verify default configuration starts in PAPER mode with trading disabled."""
    cfg = Settings(_env_file=None)
    assert cfg.TRADING_MODE == TradingMode.PAPER
    assert cfg.TRADING_ENABLED is False
    assert cfg.LIVE_TRADING is False

    assert cfg.STARTING_CAPITAL == 50.0
    assert cfg.MAX_RISK_PER_TRADE_PCT <= 0.05
    assert cfg.MAX_POSITION_SIZE_USD <= cfg.STARTING_CAPITAL


def test_live_mode_refuses_without_live_trading_flag():
    """Verify system throws a validation error if TRADING_MODE=LIVE but LIVE_TRADING=False."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(TRADING_MODE=TradingMode.LIVE, LIVE_TRADING=False)
    assert "CRITICAL SAFETY VIOLATION" in str(excinfo.value)


def test_sanitized_dict_masks_secrets():
    """Verify secrets are redacted in sanitized output."""
    cfg = Settings(
        BINANCE_API_KEY="abcdef1234567890",
        BINANCE_API_SECRET="secret_key_very_private",
    )
    sanitized = cfg.sanitized_dict()
    assert sanitized["BINANCE_API_KEY"] == "abcd...7890"
    assert sanitized["BINANCE_API_SECRET"] == "***REDACTED***"


def test_position_size_cannot_exceed_starting_capital():
    """Verify max position size cannot be higher than starting capital."""
    with pytest.raises(ValidationError):
        Settings(STARTING_CAPITAL=50.0, MAX_POSITION_SIZE_USD=100.0)
