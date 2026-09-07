"""
Unit and Integration Tests for WebSocket Manager and Quantitative Analytics Engine.
"""

from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from backend.app.api.websocket.ws_manager import WebSocketManager
from backend.app.database.models import EquitySnapshot, Trade
from backend.app.monitoring.performance_analytics import PerformanceAnalyticsEngine


@pytest.mark.asyncio
async def test_websocket_manager_lifecycle():
    """Test connect, broadcast, and disconnect on WebSocketManager."""
    manager = WebSocketManager()
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()

    # Connect
    await manager.connect(mock_ws)
    assert len(manager.active_connections) == 1

    # Broadcast
    await manager.broadcast("TEST_EVENT", {"foo": "bar"})
    mock_ws.send_json.assert_called_once()
    call_args = mock_ws.send_json.call_args[0][0]
    assert call_args["type"] == "TEST_EVENT"
    assert call_args["data"]["foo"] == "bar"

    # Disconnect
    manager.disconnect(mock_ws)
    assert len(manager.active_connections) == 0


def test_performance_analytics_trade_metrics():
    """Test performance analytics calculations on sample closed trades."""
    now = datetime.now(timezone.utc)
    t1 = Trade(
        trade_id="t1",
        symbol="BTCUSDT",
        side="BUY",
        entry_price=50000.0,
        exit_price=51000.0,
        quantity=0.0002,
        entry_time=now - timedelta(minutes=60),
        exit_time=now - timedelta(minutes=15),
        pnl=0.20,
        pnl_pct=0.02,
        fees=0.02,
        status="CLOSED",
        strategy_reason="Strategy -> Closed: TAKE_PROFIT",
    )
    t2 = Trade(
        trade_id="t2",
        symbol="BTCUSDT",
        side="BUY",
        entry_price=51000.0,
        exit_price=50500.0,
        quantity=0.0002,
        entry_time=now - timedelta(minutes=10),
        exit_time=now,
        pnl=-0.10,
        pnl_pct=-0.01,
        fees=0.02,
        status="CLOSED",
        strategy_reason="Strategy -> Closed: STOP_LOSS",
    )

    metrics = PerformanceAnalyticsEngine.calculate_trade_metrics([t1, t2], starting_capital=50.0)

    assert metrics["total_trades"] == 2
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate_pct"] == 50.0
    # Profit factor: 0.20 / 0.10 = 2.0
    assert metrics["profit_factor"] == 2.0
    assert metrics["expectancy_usd"] == 0.05
    assert metrics["payoff_ratio"] == 2.0
    assert metrics["average_holding_time_minutes"] == pytest.approx(27.5, rel=1e-2)
    assert metrics["exit_reasons_breakdown"]["TAKE_PROFIT"] == 1
    assert metrics["exit_reasons_breakdown"]["STOP_LOSS"] == 1


def test_performance_analytics_equity_metrics():
    """Test Sharpe, Sortino, and drawdown calculation on equity curve."""
    now = datetime.now(timezone.utc)
    s1 = EquitySnapshot(timestamp=now - timedelta(minutes=30), total_equity=50.0, available_balance=50.0)
    s2 = EquitySnapshot(timestamp=now - timedelta(minutes=15), total_equity=52.0, available_balance=52.0)
    s3 = EquitySnapshot(timestamp=now, total_equity=51.0, available_balance=51.0)

    metrics = PerformanceAnalyticsEngine.calculate_equity_metrics([s1, s2, s3], starting_capital=50.0)

    assert metrics["peak_equity"] == 52.0
    assert metrics["current_equity"] == 51.0
    # Max drawdown: (52 - 51) / 52 = 1.92%
    assert metrics["max_drawdown_pct"] == pytest.approx(1.92, rel=1e-2)
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
