"""
Integration tests for FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test /api/v1/health returns ok and correct mode."""
    from backend.app.core.config import settings
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "ok"
    assert data["mode"] == settings.TRADING_MODE.value
    assert data["trading_enabled"] == settings.TRADING_ENABLED


@pytest.mark.asyncio
async def test_status_and_kill_switch_endpoints(client: AsyncClient):
    """Test status querying and emergency kill switch workflow."""
    # 1. Check status
    response = await client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["trading_mode"] == "PAPER"
    assert data["kill_switch_active"] is False

    # 2. Trigger kill switch
    ks_res = await client.post("/api/v1/status/kill-switch")
    assert ks_res.status_code == 200
    assert ks_res.json()["status"] == "EMERGENCY_STOP_TRIGGERED"

    # 3. Check status reflects emergency stop
    status_res = await client.get("/api/v1/status")
    assert status_res.json()["kill_switch_active"] is True
    assert status_res.json()["bot_state"] == "EMERGENCY_STOP"

    # 4. Reset kill switch
    reset_res = await client.post("/api/v1/status/reset-kill-switch")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "KILL_SWITCH_RESET"


@pytest.mark.asyncio
async def test_account_summary(client: AsyncClient):
    """Test /api/v1/account/summary default starting capital."""
    response = await client.get("/api/v1/account/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["starting_capital"] == 50.0
    assert data["total_equity"] == 50.0
    assert data["base_currency"] == "USDT"


@pytest.mark.asyncio
async def test_config_endpoint(client: AsyncClient):
    """Test /api/v1/config returns sanitized configuration."""
    response = await client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert data["STARTING_CAPITAL"] == 50.0
    assert data["TRADING_MODE"] == "PAPER"


@pytest.mark.asyncio
async def test_execute_trade_now_endpoint(client: AsyncClient, monkeypatch):
    """Test immediate execution endpoint opens and tracks position."""
    from backend.app.execution.exchange_interface import TickerData
    from backend.app.execution.order_manager import order_manager
    from backend.app.execution.trading_bot import bot_engine

    order_manager.reset_paper_account(50.0)

    mock_ticker = TickerData(
        symbol="BTCUSDT",
        price=60000.0,
        bid_price=59995.0,
        ask_price=60005.0,
        volume_24h=500.0,
        price_change_24h_pct=1.2,
        timestamp=1700000000000,
    )
    async def mock_get_live_ticker(symbol: str):
        return mock_ticker

    monkeypatch.setattr(bot_engine.market_engine, "get_live_ticker", mock_get_live_ticker)

    response = await client.post("/api/v1/trading/trade/execute-now?symbol=BTCUSDT&side=BUY")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "order" in data
    assert data["position"]["symbol"] == "BTCUSDT"

    # Clean up position
    order_manager.reset_paper_account(50.0)

