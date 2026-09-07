"""
Quantitative Feature Engineering Pipeline.
Transforms raw OHLCV candlestick data into high-dimensional feature matrices
with zero-lookahead bias, rigorous scaling support, and customizable target labels.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.core.logging import logger
from backend.app.features.technical_indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_returns,
    compute_rolling_volatility,
    compute_rsi,
    compute_sma,
)

FEATURE_COLUMNS: List[str] = [
    # Trend Features
    "ema_ratio_20_50",
    "ema_ratio_50_200",
    "close_to_ema20",
    "close_to_ema50",
    "close_to_ema200",
    # Momentum Features
    "rsi_14",
    "rsi_slope_3",
    "macd_norm",
    "macd_signal_norm",
    "macd_hist_norm",
    "macd_hist_slope",
    # Volatility Features
    "atr_pct",
    "bb_width",
    "bb_pct_b",
    "volatility_14p",
    "volatility_30p",
    # Volume Features
    "volume_ratio",
    "volume_price_momentum",
    # Price Returns
    "return_1p",
    "return_3p",
    "return_5p",
    "return_10p",
    # Regimes
    "regime_trend",
    "regime_volatility",
]


class FeaturePipeline:
    """Feature engineering pipeline for crypto quantitative trading."""

    @staticmethod
    def build_features(df_raw: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
        """
        Compute full technical feature set on an OHLCV DataFrame.
        Guarantees zero-lookahead bias (all calculations use strictly t <= t_0 data).
        """
        if df_raw.empty or len(df_raw) < 50:
            raise ValueError(f"Insufficient candle history. Need at least 50 candles, got {len(df_raw)}.")

        df = df_raw.copy()
        # Ensure chronological ordering
        df.sort_index(inplace=True)

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        # 1. Trend Indicators
        ema20 = compute_ema(close, 20)
        ema50 = compute_ema(close, 50)
        ema200 = compute_ema(close, 200)

        df["ema_20"] = ema20
        df["ema_50"] = ema50
        df["ema_200"] = ema200

        df["ema_ratio_20_50"] = (ema20 / ema50) - 1.0
        df["ema_ratio_50_200"] = (ema50 / ema200) - 1.0
        df["close_to_ema20"] = (close / ema20) - 1.0
        df["close_to_ema50"] = (close / ema50) - 1.0
        df["close_to_ema200"] = (close / ema200) - 1.0

        # 2. Momentum Indicators
        rsi = compute_rsi(close, 14)
        df["rsi_14"] = rsi
        df["rsi_slope_3"] = rsi - rsi.shift(3)

        macd, macd_sig, macd_hist = compute_macd(close, 12, 26, 9)
        # Normalize MACD by price to make it scale-invariant across price levels
        df["macd_norm"] = macd / close
        df["macd_signal_norm"] = macd_sig / close
        df["macd_hist_norm"] = macd_hist / close
        df["macd_hist_slope"] = df["macd_hist_norm"] - df["macd_hist_norm"].shift(2)

        # 3. Volatility Indicators
        atr = compute_atr(high, low, close, 14)
        df["atr_14"] = atr
        df["atr_pct"] = atr / close

        bb_up, bb_mid, bb_low, bb_width, bb_pct_b = compute_bollinger_bands(close, 20, 2.0)
        df["bb_upper"] = bb_up
        df["bb_middle"] = bb_mid
        df["bb_lower"] = bb_low
        df["bb_width"] = bb_width
        df["bb_pct_b"] = bb_pct_b

        # 4. Multi-period Returns & Rolling Volatility
        returns_df = compute_returns(close, (1, 3, 5, 10))
        for col in returns_df.columns:
            df[col] = returns_df[col]

        vol_df = compute_rolling_volatility(df["return_1p"], (14, 30))
        for col in vol_df.columns:
            df[col] = vol_df[col]

        # 5. Volume Dynamics
        vol_sma20 = compute_sma(volume, 20)
        df["volume_sma_20"] = vol_sma20
        df["volume_ratio"] = volume / vol_sma20.replace(0, np.nan)
        df["volume_price_momentum"] = df["volume_ratio"] * df["return_1p"]

        # 6. Market Regime Classification
        # Trend: 1 = Bullish (EMA20 > EMA50 > EMA200), -1 = Bearish (EMA20 < EMA50 < EMA200), 0 = Ranging
        bullish_mask = (ema20 > ema50) & (ema50 > ema200)
        bearish_mask = (ema20 < ema50) & (ema50 < ema200)
        df["regime_trend"] = 0
        df.loc[bullish_mask, "regime_trend"] = 1
        df.loc[bearish_mask, "regime_trend"] = -1

        # Volatility Regime: 1 = High, -1 = Low, 0 = Normal (based on rolling 50-period percentile)
        atr_pct_q75 = df["atr_pct"].rolling(50, min_periods=20).quantile(0.75)
        atr_pct_q25 = df["atr_pct"].rolling(50, min_periods=20).quantile(0.25)
        df["regime_volatility"] = 0
        df.loc[df["atr_pct"] > atr_pct_q75, "regime_volatility"] = 1
        df.loc[df["atr_pct"] < atr_pct_q25, "regime_volatility"] = -1

        if drop_na:
            df.dropna(subset=FEATURE_COLUMNS, inplace=True)

        return df

    @staticmethod
    def create_classification_target(
        df_features: pd.DataFrame,
        horizon_candles: int = 4,
        return_threshold: float = 0.005,
        stop_loss_threshold: float = 0.010,
    ) -> pd.Series:
        """
        Construct binary classification target:
        Target = 1 (BUY opportunity): Forward return achieves +return_threshold within N candles
                 WITHOUT first breaching -stop_loss_threshold.
        Target = 0 (HOLD / NO TRADE): Asset does not achieve threshold or stops out.
        """
        close = df_features["close"].astype(float)
        target = pd.Series(0, index=df_features.index, name="target")

        # Forward rolling max and min prices over next horizon_candles
        # Note: target is ONLY used in historical training datasets and never during live inference.
        for i in range(len(close) - horizon_candles):
            current_price = close.iloc[i]
            future_window = close.iloc[i + 1 : i + 1 + horizon_candles]

            max_future_return = (future_window.max() - current_price) / current_price
            min_future_return = (future_window.min() - current_price) / current_price

            # Check if stop loss was hit before take profit
            if max_future_return >= return_threshold and min_future_return > -stop_loss_threshold:
                target.iloc[i] = 1

        # The last `horizon_candles` candles cannot have a confirmed target
        target.iloc[-horizon_candles:] = np.nan
        return target

    @staticmethod
    def get_latest_feature_vector(df_features: pd.DataFrame) -> Tuple[pd.Series, dict]:
        """
        Extract the most recent complete feature vector for live model inference.
        Returns (feature_series, metadata_dict).
        """
        if df_features.empty:
            raise ValueError("Empty feature DataFrame provided.")

        latest_row = df_features.iloc[-1]
        features = latest_row[FEATURE_COLUMNS]

        meta = {
            "timestamp": str(latest_row.name),
            "close": float(latest_row["close"]),
            "rsi": float(latest_row["rsi_14"]),
            "trend_regime": int(latest_row["regime_trend"]),
            "volatility_regime": int(latest_row["regime_volatility"]),
            "atr_pct": float(latest_row["atr_pct"]),
            "bb_width": float(latest_row["bb_width"]),
        }
        return features, meta
