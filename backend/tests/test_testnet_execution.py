"""
Unit and Integration Tests for Binance Testnet Execution and Safety Constraint Routing.
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.app.core.config import settings
from backend.app.execution.binance_client import BinanceClient
from backend.app.execution.order_manager import OrderManager


def test_binance_client_signature_generation():
    """Test HMAC-SHA256 cryptographic request signing for Testnet/Live endpoints."""
    client = BinanceClient(
        api_key="test_api_key",
        api_secret="test_secret_key_12345",
        testnet=True,
    )

    query_str = "symbol=BTCUSDT&timestamp=1600000000000"
    signature = client._generate_signature(query_str)

    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 output is 64 hex characters


def test_binance_client_requires_secret_for_signature():
    """Verify that attempting to sign without secret raises ValueError."""
    client = BinanceClient(api_key="key_only", api_secret="", testnet=True)
    with pytest.raises(ValueError):
        client._generate_signature("test=1")


@pytest.mark.asyncio
async def test_order_manager_safety_flag_routing():
    """Verify OrderManager refuses live execution if TRADING_ENABLED or LIVE_TRADING is false."""
    mgr = OrderManager()

    # In default test config (PAPER mode), is_live_or_testnet must be False
    assert mgr.is_live_or_testnet() is False


@pytest.mark.asyncio
async def test_binance_client_system_status_mock():
    """Test BinanceClient get_system_status response format."""
    client = BinanceClient(testnet=True)

    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"serverTime": 1700000000000}
        status = await client.get_system_status()

        assert status["status"] == "ONLINE"
        assert status["testnet"] is True
        assert "latency_ms" in status


@pytest.mark.asyncio
async def test_binance_client_account_info_security_check():
    """Test get_account_info correctly identifies and verifies withdrawal permission is disabled."""
    client = BinanceClient(api_key="mock_key", api_secret="mock_secret", testnet=True)

    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {
            "makerCommission": 10,
            "takerCommission": 10,
            "canTrade": True,
            "canWithdraw": False,  # Security rule
            "canDeposit": True,
            "accountType": "SPOT",
            "balances": [
                {"asset": "USDT", "free": "100.0", "locked": "0.0"},
                {"asset": "BTC", "free": "0.005", "locked": "0.0"},
            ],
        }

        acc = await client.get_account_info()
        assert acc["can_trade"] is True
        assert acc["can_withdraw"] is False
        assert acc["balances"]["USDT"] == 100.0
        assert acc["balances"]["BTC"] == 0.005
