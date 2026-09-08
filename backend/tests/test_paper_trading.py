"""
Unit and Integration Tests for Paper Trading Simulator, Order Manager, and Autonomous Bot Engine.
"""

import pytest
from backend.app.execution.paper_trading import PaperExchangeSimulator, PaperPosition
from backend.app.execution.order_manager import OrderManager
from backend.app.execution.trading_bot import TradingBotEngine


def test_paper_simulator_market_buy():
    """Test simulated market buy execution, fee deduction, and slippage."""
    sim = PaperExchangeSimulator(starting_capital=50.0, fee_rate=0.001, slippage_rate=0.0005)

    # Buy with $10
    res = sim.execute_market_buy(
        symbol="BTCUSDT",
        price=50000.0,
        position_size_usd=10.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        model_probability=0.65,
        strategy_reason="High confidence ML + EMA bull cross",
    )

    assert res["status"] == "FILLED"
    assert sim.active_position is not None
    # Entry price should have upward slippage (+0.05%) -> 50000 * 1.0005 = 50025.0
    assert res["entry_price"] == pytest.approx(50025.0, rel=1e-3)
    # Fee should be $0.01 (0.10% of $10)
    assert res["fee_usd"] == pytest.approx(0.01, rel=1e-3)
    # Remaining USDT balance should be $40.00
    assert sim.usdt_balance == pytest.approx(40.0, rel=1e-3)


def test_paper_simulator_market_sell_profit():
    """Test market sell execution with profit and fee calculation."""
    sim = PaperExchangeSimulator(starting_capital=50.0, fee_rate=0.001, slippage_rate=0.0005)

    sim.execute_market_buy(
        symbol="BTCUSDT",
        price=50000.0,
        position_size_usd=10.0,
        stop_loss=49000.0,
        take_profit=52000.0,
    )

    # Sell at 52000
    close_summary = sim.execute_market_sell(exit_price=52000.0, exit_reason="TAKE_PROFIT")

    assert close_summary is not None
    assert sim.active_position is None
    assert close_summary["status"] == "CLOSED"
    assert close_summary["exit_reason"] == "TAKE_PROFIT"
    # PnL should be positive
    assert close_summary["pnl"] > 0.0
    # Total equity should be > $50.00
    assert sim.usdt_balance > 50.0


def test_paper_simulator_stop_loss_trigger():
    """Test intrabar stop-loss triggering when candle low pierces stop loss."""
    sim = PaperExchangeSimulator(starting_capital=50.0)

    sim.execute_market_buy(
        symbol="BTCUSDT",
        price=50000.0,
        position_size_usd=10.0,
        stop_loss=49000.0,
        take_profit=52000.0,
    )

    # Candle dips to 48800 (below 49000 SL)
    triggered = sim.check_intrabar_triggers(current_price=49200.0, candle_high=50100.0, candle_low=48800.0)

    assert triggered is not None
    assert triggered["exit_reason"] == "STOP_LOSS"
    assert sim.active_position is None
    assert triggered["pnl"] < 0.0


def test_paper_simulator_take_profit_trigger():
    """Test intrabar take-profit triggering when candle high crosses take profit."""
    sim = PaperExchangeSimulator(starting_capital=50.0)

    sim.execute_market_buy(
        symbol="BTCUSDT",
        price=50000.0,
        position_size_usd=10.0,
        stop_loss=49000.0,
        take_profit=52000.0,
    )

    # Candle spikes to 52500 (above 52000 TP)
    triggered = sim.check_intrabar_triggers(current_price=51800.0, candle_high=52500.0, candle_low=49900.0)

    assert triggered is not None
    assert triggered["exit_reason"] == "TAKE_PROFIT"
    assert sim.active_position is None
    assert triggered["pnl"] > 0.0


def test_paper_simulator_reset():
    """Test resetting paper account to clean initial capital."""
    sim = PaperExchangeSimulator(starting_capital=50.0)
    sim.execute_market_buy(
        symbol="BTCUSDT",
        price=50000.0,
        position_size_usd=10.0,
    )

    assert sim.active_position is not None
    sim.reset_account(starting_capital=50.0)

    assert sim.active_position is None
    assert sim.usdt_balance == 50.0
    assert sim.realized_pnl_total == 0.0


@pytest.mark.asyncio
async def test_order_manager_lifecycle():
    """Test OrderManager position opening and closing workflow."""
    mgr = OrderManager()
    mgr.reset_paper_account(50.0)

    # Open position
    res = await mgr.open_position(
        symbol="BTCUSDT",
        price=60000.0,
        position_size_usd=10.0,
        stop_loss=58500.0,
        take_profit=63000.0,
    )
    assert res["status"] == "FILLED"

    pos = mgr.get_active_position()
    assert pos is not None
    assert pos["symbol"] == "BTCUSDT"

    # Close position
    close_res = await mgr.close_position(exit_price=61000.0, exit_reason="MANUAL_CLOSE")
    assert close_res is not None
    assert mgr.get_active_position() is None


@pytest.mark.asyncio
async def test_trading_bot_engine_start_stop():
    """Test TradingBotEngine start and stop cycle."""
    bot = TradingBotEngine(symbol="BTCUSDT", timeframe="15m", tick_interval_sec=0.1)

    start_res = await bot.start()
    assert start_res["status"] == "STARTED"
    assert bot.is_running is True

    status_snap = bot.get_status()
    assert status_snap["is_running"] is True
    assert status_snap["symbol"] == "BTCUSDT"

    stop_res = await bot.stop()
    assert stop_res["status"] == "STOPPED"
    assert bot.is_running is False


@pytest.mark.asyncio
async def test_market_data_engine_get_live_ticker(monkeypatch):
    """Test get_live_ticker returns valid TickerData from exchange client."""
    from backend.app.data.market_data import MarketDataEngine
    from backend.app.execution.exchange_interface import TickerData

    mock_ticker = TickerData(
        symbol="BTCUSDT",
        price=65000.0,
        bid_price=64995.0,
        ask_price=65005.0,
        volume_24h=1200.0,
        price_change_24h_pct=2.5,
        timestamp=1700000000000,
    )

    engine = MarketDataEngine()
    async def mock_get_ticker(symbol: str):
        return mock_ticker

    async def mock_init():
        pass

    monkeypatch.setattr(engine.client, "initialize", mock_init)
    monkeypatch.setattr(engine.client, "get_ticker", mock_get_ticker)

    result = await engine.get_live_ticker("BTCUSDT")
    assert result.symbol == "BTCUSDT"
    assert result.price == 65000.0
    assert result.bid_price == 64995.0

