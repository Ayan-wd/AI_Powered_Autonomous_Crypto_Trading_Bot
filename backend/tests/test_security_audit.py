"""
Unit and Integration Tests for Security Utilities, Rate Limiting, and Resilience Audit.
"""

import asyncio
import pytest
from backend.app.core.rate_limiter import TokenBucketRateLimiter, retry_with_backoff
from backend.app.core.security import mask_api_key, mask_secret, sanitize_dict, is_live_trading_allowed
from backend.app.monitoring.resilience import ResilienceWatchdog


def test_key_and_secret_masking():
    """Verify credentials masking rules."""
    assert mask_api_key("1234567890abcdef") == "1234...cdef"
    assert mask_api_key("short") == "***MASKED***"
    assert mask_api_key(None) == "NOT_CONFIGURED"

    assert mask_secret("supersecretsecretkey") == "************************"
    assert mask_secret(None) == "NOT_CONFIGURED"


def test_sanitize_dict_recursive():
    """Verify recursive dictionary masking of sensitive credential keys."""
    raw_config = {
        "binance_api_key": "my_super_real_api_key_12345",
        "binance_api_secret": "my_super_secret_password_xyz",
        "nested": {
            "jwt_token": "bearer eyJhbGciOi...",
            "db_password": "rootpassword123",
            "safe_number": 42,
        },
        "public_symbol": "BTCUSDT",
    }

    sanitized = sanitize_dict(raw_config)
    assert sanitized["public_symbol"] == "BTCUSDT"
    assert sanitized["nested"]["safe_number"] == 42
    assert "..." in sanitized["binance_api_key"]
    assert sanitized["binance_api_secret"] == "************************"
    assert sanitized["nested"]["jwt_token"] == "************************"
    assert sanitized["nested"]["db_password"] == "************************"


def test_dual_flag_safety_rule():
    """Verify is_live_trading_allowed strictly requires all 3 criteria."""
    assert is_live_trading_allowed("LIVE", True, True) is True
    assert is_live_trading_allowed("LIVE", False, True) is False
    assert is_live_trading_allowed("LIVE", True, False) is False
    assert is_live_trading_allowed("PAPER", True, True) is False
    assert is_live_trading_allowed("TESTNET", True, True) is False


@pytest.mark.asyncio
async def test_token_bucket_rate_limiter():
    """Verify TokenBucketRateLimiter token acquisition and status."""
    limiter = TokenBucketRateLimiter(rate_limit_per_second=100.0, capacity=10.0)

    # Acquire 5 tokens
    await limiter.acquire(5.0)
    status = limiter.get_status()

    assert status["total_requests_processed"] == 1
    assert status["available_tokens"] <= 5.1
    assert status["is_healthy"] is True


@pytest.mark.asyncio
async def test_retry_with_backoff():
    """Verify retry_with_backoff succeeds on transient failure."""
    attempts = 0

    async def flaky_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Temporary timeout")
        return "SUCCESS"

    result = await retry_with_backoff(flaky_api_call, max_retries=3, initial_delay=0.01)
    assert result == "SUCCESS"
    assert attempts == 2


@pytest.mark.asyncio
async def test_resilience_watchdog_audit():
    """Verify ResilienceWatchdog runs system audit cleanly."""
    watchdog = ResilienceWatchdog()
    audit = await watchdog.perform_full_system_audit()

    assert "overall_status" in audit
    assert "database" in audit
    assert "security_constraints" in audit
    assert "rate_limiter" in audit
