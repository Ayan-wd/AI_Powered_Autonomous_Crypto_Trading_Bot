"""
Real-Time Inference Engine.
Calculates calibrated buy/hold/sell probability distributions, confidence levels,
and numerical feature justifications for the trading strategy engine.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.features.feature_engineering import FEATURE_COLUMNS, FeaturePipeline
from backend.app.ml.model_manager import model_manager


class PredictionEngine:
    """Inference engine for real-time cryptocurrency trading signals."""

    @staticmethod
    def predict_from_dataframe(df_candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate model predictions from raw OHLCV candles DataFrame.
        """
        if df_candles.empty or len(df_candles) < 50:
            raise ValueError(f"Need at least 50 historical candles for ML feature calculation, got {len(df_candles)}")

        df_features = FeaturePipeline.build_features(df_candles, drop_na=False)
        features, meta = FeaturePipeline.get_latest_feature_vector(df_features)

        return PredictionEngine.predict_from_features(features, meta)

    @staticmethod
    def predict_from_features(features: pd.Series, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run inference on a single feature vector and generate deterministic reasoning.
        """
        meta = meta or {}
        model, scaler, model_metadata = model_manager.load_model()

        # If model is available on disk, run XGBoost forward pass
        if model is not None and scaler is not None:
            # Create a 1-row DataFrame preserving feature names
            df_feat = pd.DataFrame([features[FEATURE_COLUMNS].to_dict()])[FEATURE_COLUMNS]
            df_feat.fillna(0.0, inplace=True)

            feat_scaled = scaler.transform(df_feat)
            proba = model.predict_proba(feat_scaled)[0]  # [P(0), P(1)]

            buy_prob = float(proba[1])
            sell_prob = float(proba[0] * 0.3)  # Sell pressure heuristic from negative class
            hold_prob = float(1.0 - buy_prob - sell_prob)
            hold_prob = max(0.0, min(1.0, hold_prob))

            model_version = model_metadata.get("model_version", "xgb_v1.0")
        else:
            # Quantitative heuristic fallback when model weights are not yet generated
            rsi = float(features.get("rsi_14", 50.0))
            ema20_50 = float(features.get("ema_ratio_20_50", 0.0))
            return_1p = float(features.get("return_1p", 0.0))
            vol_ratio = float(features.get("volume_ratio", 1.0))

            score = 0.50
            if rsi < 35:
                score += 0.15  # Oversold bounce potential
            elif rsi > 70:
                score -= 0.15  # Overbought exhaustion

            if ema20_50 > 0.002:
                score += 0.10  # Bullish alignment
            elif ema20_50 < -0.002:
                score -= 0.10  # Bearish breakdown

            if vol_ratio > 1.5 and return_1p > 0:
                score += 0.10  # High volume upward impulse

            buy_prob = float(np.clip(score, 0.05, 0.95))
            sell_prob = float(np.clip(1.0 - buy_prob - 0.20, 0.05, 0.50))
            hold_prob = float(max(0.0, 1.0 - buy_prob - sell_prob))
            model_version = "quantitative_heuristic_v0"

        # Determine decision based on confidence hurdle threshold
        confidence_threshold = settings.MIN_PREDICTION_CONFIDENCE
        if buy_prob >= confidence_threshold:
            decision = "BUY"
            confidence = buy_prob
        elif sell_prob >= confidence_threshold:
            decision = "SELL"
            confidence = sell_prob
        else:
            decision = "HOLD / NO TRADE"
            confidence = hold_prob

        # Generate factual deterministic explanations from actual numerical features
        reasoning = PredictionEngine._generate_factual_reasoning(features, buy_prob, confidence_threshold)

        return {
            "symbol": settings.TRADING_SYMBOL,
            "timestamp": meta.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "decision": decision,
            "probabilities": {
                "buy": round(buy_prob, 4),
                "sell": round(sell_prob, 4),
                "hold": round(hold_prob, 4),
            },
            "confidence": round(confidence, 4),
            "confidence_threshold": confidence_threshold,
            "expected_return_pct": round((buy_prob - 0.5) * 1.5, 3),
            "model_version": model_version,
            "reasoning": reasoning,
            "features_snapshot": {
                "rsi_14": round(float(features.get("rsi_14", 50.0)), 2),
                "ema_ratio_20_50": round(float(features.get("ema_ratio_20_50", 0.0)), 4),
                "atr_pct": round(float(features.get("atr_pct", 0.0)), 4),
                "bb_width": round(float(features.get("bb_width", 0.0)), 4),
                "volume_ratio": round(float(features.get("volume_ratio", 1.0)), 2),
                "regime_trend": int(features.get("regime_trend", 0)),
                "regime_volatility": int(features.get("regime_volatility", 0)),
            },
        }

    @staticmethod
    def _generate_factual_reasoning(features: pd.Series, buy_prob: float, threshold: float) -> List[str]:
        """Construct factual explanation statements based purely on computed numbers."""
        reasons = []

        rsi = float(features.get("rsi_14", 50.0))
        ema20_50 = float(features.get("ema_ratio_20_50", 0.0))
        vol_ratio = float(features.get("volume_ratio", 1.0))
        trend_regime = int(features.get("regime_trend", 0))

        reasons.append(f"Model BUY probability: {buy_prob * 100:.1f}% (Hurdle threshold: {threshold * 100:.1f}%)")

        if trend_regime == 1:
            reasons.append(f"Bullish Trend: EMA20 > EMA50 > EMA200 with EMA20/50 spread at +{ema20_50 * 100:.2f}%")
        elif trend_regime == -1:
            reasons.append(f"Bearish Trend: EMA20 < EMA50 < EMA200 with EMA20/50 spread at {ema20_50 * 100:.2f}%")
        else:
            reasons.append("Trend Regime: Ranging / Neutral (Moving averages compressed)")

        if rsi > 70:
            reasons.append(f"RSI (14) at {rsi:.1f} indicating overbought conditions")
        elif rsi < 30:
            reasons.append(f"RSI (14) at {rsi:.1f} indicating oversold mean-reversion setup")
        else:
            reasons.append(f"RSI (14) at {rsi:.1f} within normal operating corridor (30–70)")

        if vol_ratio >= 1.2:
            reasons.append(f"Volume surge: {vol_ratio:.1f}x higher than 20-period moving average")
        else:
            reasons.append(f"Volume ratio: {vol_ratio:.2f}x average volume (Standard liquidity)")

        if buy_prob < threshold:
            reasons.append("Capital preservation filter: Probability below entry threshold -> HOLD")

        return reasons
