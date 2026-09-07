"""
Unit tests for database models and repositories.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.models import Candle, EquitySnapshot, Trade
from backend.app.database.repositories import CandleRepository, EquityRepository, LogRepository, TradeRepository


@pytest.mark.asyncio
async def test_trade_repository_crud(db_session: AsyncSession):
    """Test creating and retrieving trades."""
    repo = TradeRepository(db_session)

    new_trade = Trade(
        trade_id="TRD-2026-001",
        symbol="BTCUSDT",
        side="BUY",
        entry_price=92000.0,
        exit_price=92500.0,
        quantity=0.0001,
        pnl=0.05,
        pnl_pct=0.54,
        fees=0.005,
        slippage=0.001,
        model_probability=0.74,
        strategy_reason="ML Prob 74% + EMA20 > EMA50 + RSI 54",
        status="CLOSED",
        is_paper=True,
    )

    created = await repo.create(new_trade)
    assert created.id is not None
    assert created.trade_id == "TRD-2026-001"

    fetched = await repo.get_by_id("TRD-2026-001")
    assert fetched is not None
    assert fetched.symbol == "BTCUSDT"
    assert fetched.pnl == 0.05

    all_trades = await repo.get_all(is_paper=True)
    assert len(all_trades) == 1


@pytest.mark.asyncio
async def test_equity_repository(db_session: AsyncSession):
    """Test equity snapshot repository."""
    repo = EquityRepository(db_session)

    snapshot = EquitySnapshot(
        total_equity=50.50,
        available_balance=50.50,
        unrealized_pnl=0.0,
        realized_pnl=0.50,
        drawdown_pct=0.0,
        high_water_mark=50.50,
        mode="PAPER",
    )
    await repo.create(snapshot)

    latest = await repo.get_latest()
    assert latest is not None
    assert latest.total_equity == 50.50


@pytest.mark.asyncio
async def test_candle_repository(db_session: AsyncSession):
    """Test candle bulk insertion and retrieval."""
    repo = CandleRepository(db_session)

    candles = [
        Candle(
            symbol="BTCUSDT",
            timeframe="15m",
            timestamp=datetime(2026, 1, 1, 0, i * 15, tzinfo=timezone.utc),
            open=90000.0 + i * 10,
            high=90100.0 + i * 10,
            low=89950.0 + i * 10,
            close=90050.0 + i * 10,
            volume=15.5,
            is_closed=True,
        )
        for i in range(3)
    ]

    await repo.insert_bulk(candles)
    fetched = await repo.get_latest_candles("BTCUSDT", "15m", limit=10)
    assert len(fetched) == 3
