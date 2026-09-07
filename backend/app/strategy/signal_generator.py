"""
Multi-Factor Signal Generator.
Combines XGBoost probability outputs with technical indicators, regime filters,
and expected return vs transaction cost hurdle rates.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.features.feature_engineering import FeaturePipeline
from backend.app.ml.predict import PredictionEngine


class SignalGenerator:
    """Evaluates multi-factor market data and generates candidate trading signals."""

    def __init__(
        self,
        min_prediction_confidence: float = 0.65,
        estimated_cost_hurdle_pct: float = 0.003,  # 0.30% minimum expected profit hurdle (covering 2x fee + 2x slippage)
    ):
        self.min_confidence = min_prediction_confidence
        self.cost_hurdle = estimated_cost_hurdle_pct

    def generate_signal(self, df_candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate full multi-factor pipeline and return raw candidate signal.
        """
        if df_candles.empty or len(df_candles) < 50:
            return {
                "signal": "HOLD / NO TRADE",
                "raw_action": "HOLD",
                "confidence": 0.0,
                "reason": "Insufficient historical candles for feature calculation.",
                "reasons_list": ["Need at least 50 candles for feature matrix"],
            }

        # 1. Compute ML prediction and probabilities
        pred = PredictionEngine.predict_from_dataframe(df_candles)
        buy_prob = pred["probabilities"]["buy"]
        sell_prob = pred["probabilities"]["sell"]
        decision = pred["decision"]
        confidence = pred["confidence"]
        expected_ret = pred["expected_return_pct"] / 100.0  # Decimal form
        reasoning = pred["reasoning"]

        # 2. Extract technical feature snapshot
        df_features = FeaturePipeline.build_features(df_candles, drop_na=False)
        latest_features, _ = FeaturePipeline.get_latest_feature_vector(df_features)

        rsi = float(latest_features.get("rsi_14", 50.0))
        trend_regime = int(latest_features.get("regime_trend", 0))
        vol_regime = int(latest_features.get("regime_volatility", 0))
        close_p = float(latest_features.get("close", 0.0))
        atr_14 = float(latest_features.get("atr_14", 0.0))

        # 3. Deterministic Filter Logic
        # Condition A: Machine learning buy confidence
        is_ml_buy = buy_prob >= self.min_confidence

        # Condition B: Hurdle rate (expected return exceeds transaction costs)
        is_profitable_hurdle = expected_ret > self.cost_hurdle

        # Condition C: Regime filter (no buy in strong downtrend unless extreme oversold bounce RSI < 28)
        is_trend_acceptable = (trend_regime >= 0) or (trend_regime == -1 and rsi < 28.0)

        # Condition D: Overbought exhaustion guard (RSI < 72)
        is_not_overbought = rsi < 72.0

        if is_ml_buy and is_profitable_hurdle and is_trend_acceptable and is_not_overbought:
            return {
                "signal": "BUY",
                "raw_action": "BUY",
                "confidence": confidence,
                "expected_return_pct": expected_ret * 100.0,
                "current_price": close_p,
                "atr": atr_14,
                "reason": f"ML Buy Prob ({buy_prob * 100:.1f}%) > {self.min_confidence * 100:.1f}%, Expected return exceeds fee hurdle.",
                "reasons_list": reasoning,
            }

        elif sell_prob >= self.min_confidence or (trend_regime == -1 and rsi > 70):
            return {
                "signal": "SELL",
                "raw_action": "SELL",
                "confidence": max(sell_prob, 0.70),
                "expected_return_pct": 0.0,
                "current_price": close_p,
                "atr": atr_14,
                "reason": "Bearish setup / Overbought exhaustion detected.",
                "reasons_list": reasoning,
            }

        return {
            "signal": "HOLD / NO TRADE",
            "raw_action": "HOLD",
            "confidence": pred["probabilities"]["hold"],
            "expected_return_pct": 0.0,
            "current_price": close_p,
            "atr": atr_14,
            "reason": "Market setup does not meet statistical entry threshold -> Capital Preserved.",
            "reasons_list": reasoning,
        }
