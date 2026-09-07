"""
Unit tests for Technical Indicators and Feature Engineering Pipeline.
Includes strict Zero-Lookahead Bias invariant testing.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest
from backend.app.features.feature_engineering import FEATURE_COLUMNS, FeaturePipeline
from backend.app.features.technical_indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_returns,
    compute_rsi,
    compute_sma,
)


def generate_synthetic_ohlcv(n_bars: int = 100) -> pd.DataFrame:
    """Generate realistic synthetic OHLCV data for testing."""
    np.random.seed(42)
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    dates = [start_time + timedelta(minutes=15 * i) for i in range(n_bars)]

    # Geometric random walk
    returns = np.random.normal(loc=0.0002, scale=0.005, size=n_bars)
    prices = 90000.0 * np.cumprod(1 + returns)

    highs = prices * (1 + np.abs(np.random.normal(0, 0.002, n_bars)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.002, n_bars)))
    opens = (highs + lows) / 2.0
    volumes = np.random.uniform(5.0, 50.0, n_bars)

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


def test_ema_and_sma():
    """Verify EMA and SMA basic properties."""
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    sma3 = compute_sma(series, 3)
    assert np.isnan(sma3.iloc[0])
    assert np.isnan(sma3.iloc[1])
    assert sma3.iloc[2] == 20.0
    assert sma3.iloc[4] == 40.0

    ema3 = compute_ema(series, 3)
    assert len(ema3) == 5
    assert ema3.iloc[-1] > ema3.iloc[0]


def test_rsi_bounds():
    """Verify RSI produces values within [0, 100]."""
    df = generate_synthetic_ohlcv(60)
    rsi = compute_rsi(df["close"], 14)
    assert rsi.min() >= 0.0
    assert rsi.max() <= 100.0
    assert not rsi.isna().any()


def test_macd_and_atr():
    """Verify MACD and ATR calculations."""
    df = generate_synthetic_ohlcv(60)
    macd, signal, hist = compute_macd(df["close"])
    assert len(macd) == 60
    assert len(hist) == 60
    # histogram should be exactly macd - signal
    np.testing.assert_allclose(hist.values, (macd - signal).values, rtol=1e-5)

    atr = compute_atr(df["high"], df["low"], df["close"], 14)
    assert (atr > 0).all()


def test_feature_pipeline_builds_all_columns():
    """Verify FeaturePipeline builds all defined feature columns without errors."""
    df = generate_synthetic_ohlcv(120)
    df_features = FeaturePipeline.build_features(df, drop_na=True)

    for col in FEATURE_COLUMNS:
        assert col in df_features.columns, f"Missing feature column: {col}"
    assert len(df_features) > 0


def test_zero_lookahead_bias_invariant():
    """
    CRITICAL QUANTITATIVE INVARIANT TEST:
    Verifies that changing future bars (t > T) does NOT alter the feature values computed at time T.
    """
    df1 = generate_synthetic_ohlcv(100)
    df2 = df1.copy()

    # Modify future data after index 60
    df2.iloc[60:, df2.columns.get_loc("close")] *= 2.0
    df2.iloc[60:, df2.columns.get_loc("high")] *= 2.0
    df2.iloc[60:, df2.columns.get_loc("low")] *= 2.0

    feats1 = FeaturePipeline.build_features(df1, drop_na=False)
    feats2 = FeaturePipeline.build_features(df2, drop_na=False)

    # Features at or before index 59 MUST be mathematically identical
    slice1 = feats1.iloc[:60][FEATURE_COLUMNS].values
    slice2 = feats2.iloc[:60][FEATURE_COLUMNS].values

    np.testing.assert_allclose(
        slice1,
        slice2,
        rtol=1e-7,
        atol=1e-7,
        err_msg="Lookahead bias detected! Changing future prices altered historical feature values.",
    )


def test_classification_target_generation():
    """Verify classification target generation logic."""
    df = generate_synthetic_ohlcv(80)
    df_features = FeaturePipeline.build_features(df, drop_na=False)
    target = FeaturePipeline.create_classification_target(
        df_features, horizon_candles=4, return_threshold=0.005
    )

    # Target should be series of 0s and 1s, with trailing NaNs
    valid_target = target.dropna()
    assert set(valid_target.unique()).issubset({0, 1})
    assert np.isnan(target.iloc[-1])
