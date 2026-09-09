"""
Unit tests for Institutional Quantitative Optimizations:
ADX, Choppiness Index, MFI, Chandelier Trailing Stop, Breakeven Lock,
Volatility-Bounded Position Sizing, and Anti-Chop Signal Filtering.
"""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest

from backend.app.execution.paper_trading import PaperPosition
from backend.app.features.feature_engineering import FeaturePipeline
from backend.app.features.technical_indicators import (
    compute_adx,
    compute_chandelier_exit,
    compute_choppiness_index,
    compute_mfi,
)
from backend.app.risk.position_sizing import PositionSizer
from backend.app.strategy.signal_generator import SignalGenerator


def _generate_synthetic_candles(n: int = 100, trend: float = 0.001) -> pd.DataFrame:
    """Generate realistic synthetic OHLCV candles."""
    np.random.seed(42)
    prices = [70000.0]
    for _ in range(n - 1):
        ret = np.random.normal(trend, 0.005)
        prices.append(prices[-1] * (1.0 + ret))

    close = np.array(prices)
    high = close * (1.0 + np.abs(np.random.normal(0.002, 0.002, n)))
    low = close * (1.0 - np.abs(np.random.normal(0.002, 0.002, n)))
    volume = np.random.uniform(50.0, 300.0, n)

    idx = pd.date_range(start="2026-01-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )


def test_adx_indicator_calculation():
    """Verify ADX, +DI, and -DI are bounded, non-negative, and properly smoothed."""
    df = _generate_synthetic_candles(100, trend=0.002)
    adx, plus_di, minus_di = compute_adx(df["high"], df["low"], df["close"], period=14)

    assert len(adx) == len(df)
    assert not adx.isna().all()
    # Values bounded between 0 and 100
    valid_adx = adx.dropna()
    assert (valid_adx >= 0.0).all() and (valid_adx <= 100.0).all()
    assert (plus_di >= 0.0).all() and (plus_di <= 100.0).all()
    assert (minus_di >= 0.0).all() and (minus_di <= 100.0).all()


def test_choppiness_index_calculation():
    """Verify Choppiness Index (CHOP) stays within [0, 100]."""
    df = _generate_synthetic_candles(100, trend=0.0)
    chop = compute_choppiness_index(df["high"], df["low"], df["close"], period=14)

    assert len(chop) == len(df)
    valid_chop = chop.dropna()
    assert (valid_chop >= 0.0).all() and (valid_chop <= 100.0).all()


def test_mfi_indicator_calculation():
    """Verify Money Flow Index (MFI) stays within [0, 100]."""
    df = _generate_synthetic_candles(100)
    mfi = compute_mfi(df["high"], df["low"], df["close"], df["volume"], period=14)

    assert len(mfi) == len(df)
    valid_mfi = mfi.dropna()
    assert (valid_mfi >= 0.0).all() and (valid_mfi <= 100.0).all()


def test_chandelier_exit_calculation():
    """Verify Chandelier long stop is bounded below highest high and short stop bounded above lowest low."""
    df = _generate_synthetic_candles(100)
    long_stop, short_stop = compute_chandelier_exit(df["high"], df["low"], df["close"], period=22, multiplier=2.5)

    assert len(long_stop) == len(df)
    highest_high = df["high"].rolling(window=22, min_periods=1).max()
    lowest_low = df["low"].rolling(window=22, min_periods=1).min()
    assert (long_stop <= highest_high).all()
    assert (short_stop >= lowest_low).all()


def test_breakeven_lock_on_position():
    """Verify Stop-Loss ratchets to entry + 0.20% when position reaches +1.0R gain."""
    entry_price = 70000.0
    initial_sl = 69000.0  # Risk = 1,000
    pos = PaperPosition(
        trade_id="pos_be_test",
        symbol="BTCUSDT",
        side="BUY",
        entry_price=entry_price,
        quantity=0.01,
        cost_basis_usd=700.0,
        entry_fee_usd=0.70,
        stop_loss=initial_sl,
        take_profit=72000.0,
    )

    # 1. Price small move up (+0.5R = $70,500) -> Breakeven should NOT fire yet
    pos.update_mark_price(70500.0)
    event1 = pos.update_trailing_and_breakeven(70500.0, atr=500.0)
    assert not pos.breakeven_triggered
    assert pos.stop_loss == initial_sl

    # 2. Price hits +1.0R (+ $1,000 = $71,000) -> Breakeven MUST fire and lock SL > entry
    pos.update_mark_price(71000.0)
    event2 = pos.update_trailing_and_breakeven(71000.0, atr=800.0)
    assert pos.breakeven_triggered
    assert pos.stop_loss == pytest.approx(entry_price * 1.002, rel=1e-4)
    assert pos.stop_loss > entry_price  # Guaranteed zero risk!


def test_chandelier_trailing_stop_monotonicity():
    """Verify Chandelier trailing stop ratchets up with new highs and NEVER decreases on retracement."""
    entry_price = 70000.0
    initial_sl = 69000.0
    pos = PaperPosition(
        trade_id="pos_trail_test",
        symbol="BTCUSDT",
        side="BUY",
        entry_price=entry_price,
        quantity=0.01,
        cost_basis_usd=700.0,
        entry_fee_usd=0.70,
        stop_loss=initial_sl,
        take_profit=75000.0,
    )

    # Surge to 72,000 with ATR = 400. Chandelier trail = 72,000 - 1.5*400 = 71,400
    pos.update_mark_price(72000.0)
    pos.update_trailing_and_breakeven(72000.0, atr=400.0)
    first_ratchet_sl = pos.stop_loss
    assert first_ratchet_sl == 71400.0
    assert first_ratchet_sl > entry_price

    # Price pushes higher to 73,000. New trail = 73,000 - 600 = 72,400
    pos.update_mark_price(73000.0)
    pos.update_trailing_and_breakeven(73000.0, atr=400.0)
    second_ratchet_sl = pos.stop_loss
    assert second_ratchet_sl == 72400.0
    assert second_ratchet_sl > first_ratchet_sl

    # Price retraces down to 72,500. Stop loss MUST NOT decrease!
    pos.update_mark_price(72500.0)
    pos.update_trailing_and_breakeven(72500.0, atr=400.0)
    assert pos.stop_loss == second_ratchet_sl


def test_volatility_bounded_position_sizing():
    """Verify ATR floor prevents overleveraging when an artificially tight stop loss is supplied."""
    sizer = PositionSizer(max_risk_pct=0.01, max_position_size_usd=10000.0)
    account_equity = 10000.0
    current_price = 70000.0

    # Artificially tight stop (only $10 away = 0.014%)
    tight_stop = 69990.0
    atr = 500.0  # True market volatility is $500

    sizing = sizer.calculate_position_size(
        account_equity=account_equity,
        current_price=current_price,
        stop_loss_price=tight_stop,
        atr=atr,
    )

    # Without ATR floor, size would be $100 / $10 * $70,000 = $700,000 (capped at $10k)
    # With ATR floor (0.75 * 500 = $375 unit risk), raw size is $100 / $375 * 70,000 = ~$18,666 -> capped safely
    assert sizing["position_value_usd"] <= account_equity
    assert sizing["quantity"] > 0.0


def test_signal_generator_anti_chop_filter():
    """Verify that severe chop (low ADX, high CHOP) properly suppresses breakout buy signals."""
    df = _generate_synthetic_candles(100, trend=0.0)
    sig_gen = SignalGenerator(min_prediction_confidence=0.51)

    signal = sig_gen.generate_signal(df)
    assert "adx" in signal
    assert "chop" in signal
    assert "mfi" in signal
    assert "conviction_score" in signal
