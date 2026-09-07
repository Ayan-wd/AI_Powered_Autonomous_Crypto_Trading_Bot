"""
Unit tests for exchange interface abstraction and Binance client.
"""

import pytest
from backend.app.execution.binance_client import BinanceClient
from backend.app.execution.exchange_interface import ExchangeInterface


def test_binance_client_subclasses_exchange_interface():
    """Verify BinanceClient satisfies the abstract ExchangeInterface protocol."""
    client = BinanceClient(testnet=True)
    assert isinstance(client, ExchangeInterface)
    assert client.testnet is True
    assert "testnet" in client.base_url


def test_signature_generation():
    """Verify HMAC SHA256 signature generation."""
    client = BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)
    sig = client._generate_signature("symbol=BTCUSDT&timestamp=1700000000000")
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA256 hex string length


def test_signature_requires_secret():
    """Verify exception when attempting to sign without API secret."""
    client = BinanceClient(api_key=None, api_secret=None, testnet=True)
    with pytest.raises(ValueError):
        client._generate_signature("test_query")
