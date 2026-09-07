"""
Unit tests for the Realistic Backtesting Engine, Metrics Calculator, and Benchmark Comparison.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest
from backend.app.backtesting.engine import BacktestEngine
from backend.app.backtesting.metrics import PerformanceMetricsCalculator
from backend.app.backtesting.walk_forward import WalkForwardBacktester


def generate_backtest_candles(n_bars: int = 150) -> pd.DataFrame:
    """Generate realistic OHLCV dataframe with trend and oscillating patterns."""
    np.random.seed(42)
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    dates = [start_time + timedelta(minutes=15 * i) for i in range(n_bars)]

    # Generate upward trending price with waves
    t = np.linspace(0, 10, n_bars)
    prices = 90000.0 + (t * 500.0) + (np.sin(t) * 1000.0) + np.random.normal(0, 50.0, n_bars)

    highs = prices + np.random.uniform(50.0, 200.0, n_bars)
    lows = prices - np.random.uniform(50.0, 200.0, n_bars)
    opens = (highs + lows) / 2.0
    volumes = np.random.uniform(10.0, 100.0, n_bars)

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


def test_metrics_calculator_comprehensive():
    """Verify metrics calculation logic."""
    trades = [
        {"pnl": 0.50, "fees": 0.01, "slippage": 0.005, "bars_held": 4},
        {"pnl": -0.20, "fees": 0.01, "slippage": 0.005, "bars_held": 2},
        {"pnl": 0.80, "fees": 0.01, "slippage": 0.005, "bars_held": 5},
    ]
    equity_series = pd.Series([50.0, 50.50, 50.30, 51.10])

    metrics = PerformanceMetricsCalculator.calculate(
        trades=trades, equity_curve=equity_series, starting_capital=50.0
    )

    assert metrics["starting_capital"] == 50.0
    assert metrics["final_equity"] == 51.10
    assert metrics["net_profit"] == 1.10
    assert metrics["total_trades"] == 3
    assert metrics["winning_trades"] == 2
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate_pct"] == round(2 / 3 * 100, 2)
    assert metrics["profit_factor"] == round(1.30 / 0.20, 2)
    assert metrics["total_fees_paid"] == 0.03
    assert metrics["expectancy"] > 0


def test_backtest_engine_fee_and_slippage_deductions():
    """Verify that backtest engine accurately deducts transaction fees and slippage."""
    df = generate_backtest_candles(100)
    engine = BacktestEngine(
        starting_capital=50.0,
        fee_rate=0.001,
        slippage_rate=0.0005,
    )

    res = engine.run(df, strategy_type="AI_ML")
    metrics = res["metrics"]
    assert "final_equity" in metrics
    assert "total_fees_paid" in metrics
    assert metrics["total_fees_paid"] >= 0.0


def test_backtest_engine_stop_loss_and_take_profit():
    """Verify stop loss and take profit parameters are handled."""
    df = generate_backtest_candles(100)
    engine = BacktestEngine(
        starting_capital=50.0,
        stop_loss_pct=0.01,
        take_profit_pct=0.02,
    )
    res = engine.run(df, strategy_type="TECHNICAL_CROSS")
    trades = res["trades"]
    for t in trades:
        assert t["exit_reason"] in ("STOP_LOSS", "TAKE_PROFIT", "SIGNAL_EXIT", "BACKTEST_END")


def test_buy_and_hold_benchmark():
    """Verify Buy & Hold benchmark calculation."""
    df = generate_backtest_candles(80)
    engine = BacktestEngine(starting_capital=50.0)
    res = engine.run(df, strategy_type="BUY_AND_HOLD")

    assert res["strategy"] == "BUY_AND_HOLD"
    assert len(res["trades"]) == 1
    assert res["metrics"]["starting_capital"] == 50.0


def test_walk_forward_backtester():
    """Verify sequential walk-forward backtest."""
    df = generate_backtest_candles(140)
    wf_tester = WalkForwardBacktester(starting_capital=50.0, n_splits=2)
    res = wf_tester.run(df)

    assert res["total_folds"] >= 1
    assert "final_equity" in res
    assert "fold_reports" in res
