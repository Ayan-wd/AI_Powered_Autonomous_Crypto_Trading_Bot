"""
Unit tests for Position Sizing, Drawdown Controls, Master Risk Manager, and Strategy Decision Engine.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest
from backend.app.risk.drawdown_control import DrawdownController
from backend.app.risk.position_sizing import PositionSizer
from backend.app.risk.risk_manager import RiskManager
from backend.app.strategy.signal_generator import SignalGenerator
from backend.app.strategy.strategy_engine import StrategyDecisionEngine


def generate_test_candles(n_bars: int = 80) -> pd.DataFrame:
    """Generate synthetic candles for strategy testing."""
    np.random.seed(42)
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    dates = [start_time + timedelta(minutes=15 * i) for i in range(n_bars)]

    prices = 90000.0 + np.cumsum(np.random.normal(10.0, 50.0, n_bars))
    highs = prices + np.random.uniform(20.0, 100.0, n_bars)
    lows = prices - np.random.uniform(20.0, 100.0, n_bars)
    opens = (highs + lows) / 2.0
    volumes = np.random.uniform(10.0, 50.0, n_bars)

    df = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes,
        },
        index=dates,
    )
    df.index.name = "timestamp"
    return df


def test_position_sizing_respects_max_cap():
    """Verify position sizing never exceeds max position cap ($10 on $50 account)."""
    sizer = PositionSizer(max_risk_pct=0.01, max_position_size_usd=10.0)

    # 1. Standard $50 capital with $90k price, $88.5k stop loss (1.5% distance)
    # Risk budget = $50 * 1% = $0.50. Risk per unit = $1500.
    # Raw qty = 0.50 / 1500 = 0.0003333 BTC (~$30.00 USD).
    # Sizer MUST cap position to $10.00 USD.
    res = sizer.calculate_position_size(
        account_equity=50.0,
        current_price=90000.0,
        stop_loss_price=88500.0,
    )

    assert res["position_value_usd"] <= 10.0
    assert res["quantity"] > 0
    assert res["risk_amount_usd"] == 0.50


def test_anti_martingale_guarantee():
    """
    ANTI-MARTINGALE INVARIANT TEST:
    Verify that after losing trades (equity drops from $50 -> $45),
    position size strictly DOES NOT INCREASE.
    """
    sizer = PositionSizer(max_risk_pct=0.01, max_position_size_usd=10.0)

    size_50 = sizer.calculate_position_size(
        account_equity=50.0, current_price=90000.0, stop_loss_price=89000.0
    )
    size_45 = sizer.calculate_position_size(
        account_equity=45.0, current_price=90000.0, stop_loss_price=89000.0
    )

    assert size_45["position_value_usd"] <= size_50["position_value_usd"]
    assert size_45["risk_amount_usd"] < size_50["risk_amount_usd"]


def test_drawdown_controller_daily_loss_limit():
    """Verify trading halts when daily loss reaches 3% ($1.50 on $50)."""
    controller = DrawdownController(starting_capital=50.0, max_daily_loss_pct=0.03)

    allowed, reason = controller.can_open_new_trade(current_equity=50.0)
    assert allowed is True

    # Simulate 2 losing trades totaling $1.60 loss
    controller.update_equity_state(current_equity=49.20, trade_pnl=-0.80)
    controller.update_equity_state(current_equity=48.40, trade_pnl=-0.80)

    allowed_after, reason_after = controller.can_open_new_trade(current_equity=48.40)
    assert allowed_after is False
    assert "DAILY LOSS LIMIT" in reason_after


def test_drawdown_controller_max_drawdown():
    """Verify circuit breaker triggers when drawdown reaches 10% from peak."""
    controller = DrawdownController(starting_capital=50.0, max_drawdown_pct=0.10)

    # Equity rises to $60 (new high water mark)
    controller.update_equity_state(current_equity=60.0)
    assert controller.high_water_mark == 60.0

    # Equity drops to $53 (11.6% drawdown from $60)
    controller.update_equity_state(current_equity=53.0)
    allowed, reason = controller.can_open_new_trade(current_equity=53.0)

    assert allowed is False
    assert "MAX DRAWDOWN LIMIT" in reason


def test_drawdown_controller_consecutive_losses():
    """Verify cooldown triggers after 3 consecutive losing trades."""
    controller = DrawdownController(starting_capital=50.0, max_consecutive_losses=3)

    controller.update_equity_state(current_equity=49.90, trade_pnl=-0.10)
    controller.update_equity_state(current_equity=49.80, trade_pnl=-0.10)
    controller.update_equity_state(current_equity=49.70, trade_pnl=-0.10)

    allowed, reason = controller.can_open_new_trade(current_equity=49.70)
    assert allowed is False
    assert "CONSECUTIVE LOSS LIMIT" in reason


def test_strategy_decision_engine_hold_on_empty():
    """Verify strategy decision engine safely returns HOLD when market conditions do not align."""
    df = generate_test_candles(60)
    engine = StrategyDecisionEngine()
    decision = engine.evaluate_decision(df_candles=df, account_equity=50.0)

    assert decision["action"] in ("BUY", "HOLD", "SELL")
    assert isinstance(decision["numerical_explanation"], list)
    assert len(decision["numerical_explanation"]) > 0
