"""
Automated regression tests specifically validating the paper-trading audit fixes:
- Bug from Trade ID 3 (inverted Stop-Loss rejection)
- Full round-trip fee accounting (entry fee + exit fee)
- Bid/Ask spread execution
- Conservative Stop-Loss execution with adverse slippage (impossible profit prevention)
- Stale candle / live ticker desynchronization guards
- Profit factor and drawdown calculations
"""

from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest

from backend.app.data.market_data import is_candle_stale
from backend.app.database.models import EquitySnapshot, Trade
from backend.app.execution.order_manager import OrderManager
from backend.app.execution.paper_trading import PaperExchangeSimulator, PaperPosition
from backend.app.monitoring.performance_analytics import PerformanceAnalyticsEngine
from backend.app.risk.risk_manager import RiskManager
from backend.app.strategy.strategy_engine import StrategyDecisionEngine


def test_inverted_stop_loss_rejected_in_risk_manager():
    """Verify that RiskManager strictly rejects any BUY order where stop_loss >= current_price."""
    rm = RiskManager(starting_capital=10000.0)
    current_price = 78000.0
    inverted_stop_loss = 79000.0  # Above entry price

    eval_res = rm.evaluate_order(
        account_equity=10000.0,
        current_price=current_price,
        side="BUY",
        stop_loss_price=inverted_stop_loss,
    )

    assert eval_res["approved"] is False
    assert "DIRECTIONAL INVARIANT VIOLATION" in eval_res["reason"]


def test_inverted_stop_loss_rejected_in_paper_simulator():
    """Verify that PaperExchangeSimulator strictly refuses to fill a BUY order where stop_loss >= entry_price."""
    sim = PaperExchangeSimulator(starting_capital=10000.0)
    current_price = 78000.0
    inverted_stop_loss = 79000.0

    fill_res = sim.execute_market_buy(
        symbol="BTCUSDT",
        price=current_price,
        position_size_usd=1000.0,
        stop_loss=inverted_stop_loss,
    )

    assert fill_res["status"] == "REJECTED"
    assert "DIRECTIONAL INVARIANT VIOLATION" in fill_res["reason"]
    assert sim.active_position is None


@pytest.mark.asyncio
async def test_inverted_stop_loss_rejected_in_order_manager():
    """Verify that OrderManager catches and blocks inverted stop loss before order placement."""
    om = OrderManager()
    om.reset_paper_account(10000.0)

    res = await om.open_position(
        symbol="BTCUSDT",
        price=78000.0,
        position_size_usd=1000.0,
        stop_loss=79000.0,  # Inverted
    )

    assert res["status"] == "REJECTED"
    assert "DIRECTIONAL INVARIANT VIOLATION" in res["reason"]


def test_full_roundtrip_fee_accounting():
    """
    Verify that trade P&L accounts for BOTH the entry fee and the exit fee.
    If price does not change, P&L must be exactly -Total Fees (approx -0.20% of position).
    """
    sim = PaperExchangeSimulator(starting_capital=10000.0, fee_rate=0.001, slippage_rate=0.0)
    position_size = 1000.0
    price = 100.0

    # Entry: $1000 invested. Fee is 0.1% = $1.00. Net capital = $999.00 -> 9.99 units.
    fill = sim.execute_market_buy(
        symbol="TESTUSDT",
        price=price,
        position_size_usd=position_size,
        stop_loss=90.0,
        take_profit=120.0,
    )
    assert fill["status"] == "FILLED"
    assert fill["fee_usd"] == 1.00
    assert sim.active_position.entry_fee_usd == 1.00
    assert sim.active_position.cost_basis_usd == 1000.0

    # Exit at the same price ($100.00)
    # Gross return: 9.99 * 100 = $999.00. Exit fee: 0.1% = $0.999. Net return = $998.001.
    # Total PnL should be: $998.001 - $1000.00 = -$1.999 (approx -$2.00 total fees)
    closed = sim.execute_market_sell(exit_price=price, exit_reason="SIGNAL_EXIT")
    assert closed is not None
    assert closed["entry_fee"] == 1.00
    assert round(closed["exit_fee"], 3) == 0.999
    assert round(closed["fees"], 3) == 1.999
    assert round(closed["pnl"], 3) == -1.999  # NOT zero! Both entry and exit fees deducted.
    assert round(sim.usdt_balance, 2) == round(10000.0 - 1.999, 2)


def test_bid_ask_spread_execution():
    """Verify that paper trades execute at ask_price on buy and bid_price on sell."""
    sim = PaperExchangeSimulator(starting_capital=10000.0, fee_rate=0.0, slippage_rate=0.001)
    mid_price = 100.0
    bid_price = 99.90
    ask_price = 100.10

    # Buy should execute off ask_price * (1 + slippage)
    fill = sim.execute_market_buy(
        symbol="TESTUSDT",
        price=mid_price,
        position_size_usd=1000.0,
        stop_loss=90.0,
        take_profit=110.0,
        ask_price=ask_price,
    )
    assert fill["status"] == "FILLED"
    expected_entry = ask_price * 1.001
    assert round(fill["entry_price"], 4) == round(expected_entry, 4)

    # Sell should execute off bid_price * (1 - slippage)
    closed = sim.execute_market_sell(
        exit_price=mid_price,
        exit_reason="SIGNAL_EXIT",
        bid_price=bid_price,
    )
    expected_exit = bid_price * 0.999
    assert round(closed["exit_price"], 4) == round(expected_exit, 4)


def test_conservative_stop_loss_execution_no_phantom_profits():
    """
    Verify that an intrabar Stop-Loss trigger NEVER exits higher than the Stop-Loss price
    and models adverse slippage, ensuring phantom profits are impossible.
    """
    sim = PaperExchangeSimulator(starting_capital=10000.0, fee_rate=0.001, slippage_rate=0.0005)
    entry_price = 78000.0
    stop_loss = 77000.0
    take_profit = 80000.0

    fill = sim.execute_market_buy(
        symbol="BTCUSDT",
        price=entry_price,
        position_size_usd=1000.0,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )
    assert fill["status"] == "FILLED"

    # Price violently drops to $76,500 (breaching $77,000 SL)
    triggered = sim.check_intrabar_triggers(
        current_price=76800.0,
        candle_high=77500.0,
        candle_low=76500.0,
    )

    assert triggered is not None
    assert triggered["exit_reason"] == "STOP_LOSS"
    # Exit price must reflect the adverse breached price ($76,500) and slippage, <= stop_loss
    assert triggered["exit_price"] <= stop_loss
    assert triggered["exit_price"] < entry_price
    # PnL MUST be negative (loss), never positive!
    assert triggered["pnl"] < 0.0


def test_stale_candle_detection():
    """Verify that is_candle_stale accurately flags outdated timestamps."""
    now_utc = datetime.now(timezone.utc)

    # 1-minute candle from 10 seconds ago -> Fresh
    fresh_ts = now_utc - timedelta(seconds=10)
    assert is_candle_stale(fresh_ts, timeframe="1m") is False

    # 1-minute candle from 5 minutes ago (300s > 120s limit) -> Stale
    stale_ts = now_utc - timedelta(seconds=300)
    assert is_candle_stale(stale_ts, timeframe="1m") is True


def test_profit_factor_and_drawdown_calculation():
    """Verify profit factor avoids infinite anomalies and drawdown calculates accurately."""
    now = datetime.now(timezone.utc)

    # Trades with only wins (losses = 0)
    t1 = Trade(trade_id="t1", status="CLOSED", exit_price=105.0, pnl=50.0, pnl_pct=0.05, fees=2.0)
    metrics_wins_only = PerformanceAnalyticsEngine.calculate_trade_metrics([t1], starting_capital=10000.0)
    # Should be finite (equal to gross profit) rather than 999.0 / inf
    assert metrics_wins_only["profit_factor"] == 50.0
    assert metrics_wins_only["win_rate_pct"] == 100.0

    # Trades with wins and losses
    t2 = Trade(trade_id="t2", status="CLOSED", exit_price=95.0, pnl=-25.0, pnl_pct=-0.025, fees=2.0)
    metrics_mixed = PerformanceAnalyticsEngine.calculate_trade_metrics([t1, t2], starting_capital=10000.0)
    # Profit factor: 50.0 / 25.0 = 2.0
    assert metrics_mixed["profit_factor"] == 2.0
    assert metrics_mixed["win_rate_pct"] == 50.0

    # Equity snapshots drawdown
    s0 = EquitySnapshot(timestamp=now - timedelta(minutes=30), total_equity=10000.0, available_balance=10000.0)
    s1 = EquitySnapshot(timestamp=now - timedelta(minutes=20), total_equity=10500.0, available_balance=10500.0) # Peak
    s2 = EquitySnapshot(timestamp=now - timedelta(minutes=10), total_equity=9975.0, available_balance=9975.0)  # Trough: 525 drawdown
    eq_metrics = PerformanceAnalyticsEngine.calculate_equity_metrics([s0, s1, s2], starting_capital=10000.0)

    assert eq_metrics["peak_equity"] == 10500.0
    assert eq_metrics["max_drawdown_usd"] == 525.0
    assert eq_metrics["max_drawdown_pct"] == 5.0  # 525 / 10500 = 5.0%
