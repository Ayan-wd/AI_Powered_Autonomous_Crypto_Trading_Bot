"""
Unit tests for quantitative market data validator.
"""

from datetime import datetime, timezone
import pytest
from backend.app.data.data_validator import MarketDataValidator


def test_valid_candle():
    """Verify that logically sound candle passes validation."""
    valid_candle = {
        "timestamp": 1700000000000,
        "open": 90000.0,
        "high": 90500.0,
        "low": 89800.0,
        "close": 90200.0,
        "volume": 12.5,
    }
    is_valid, error = MarketDataValidator.validate_candle(valid_candle)
    assert is_valid is True
    assert error is None


def test_invalid_candle_high_less_than_open():
    """Verify failure when high is less than open or close."""
    invalid_candle = {
        "timestamp": 1700000000000,
        "open": 90500.0,
        "high": 90000.0,  # Invalid: high < open
        "low": 89800.0,
        "close": 90200.0,
        "volume": 12.5,
    }
    is_valid, error = MarketDataValidator.validate_candle(invalid_candle)
    assert is_valid is False
    assert "High price" in error


def test_invalid_candle_negative_price():
    """Verify failure when price is negative or zero."""
    invalid_candle = {
        "timestamp": 1700000000000,
        "open": -100.0,
        "high": 100.0,
        "low": -200.0,
        "close": 50.0,
        "volume": 1.0,
    }
    is_valid, error = MarketDataValidator.validate_candle(invalid_candle)
    assert is_valid is False
    assert "Non-positive price" in error


def test_sequence_validation_detects_gaps():
    """Verify sequence validator catches missing intervals."""
    # 15m step is 900,000 ms
    base_ts = 1700000000000
    candles = [
        {"timestamp": base_ts, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 10},
        # Missing timestamp base_ts + 900000
        {"timestamp": base_ts + 1800000, "open": 105, "high": 115, "low": 95, "close": 110, "volume": 10},
    ]
    valid_candles, issues = MarketDataValidator.validate_sequence(candles, timeframe="15m")
    assert len(valid_candles) == 2
    assert any("Data Gap Detected" in issue for issue in issues)


def test_stale_data_detector():
    """Verify stale data detection logic."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    # Candle from 3 hours ago for 15m timeframe is stale (tolerance is 2 intervals = 30m)
    old_ts = now_ms - (3 * 60 * 60 * 1000)
    assert MarketDataValidator.is_feed_stale(old_ts, timeframe="15m") is True

    # Fresh candle (1 minute ago) is not stale
    fresh_ts = now_ms - (60 * 1000)
    assert MarketDataValidator.is_feed_stale(fresh_ts, timeframe="15m") is False
