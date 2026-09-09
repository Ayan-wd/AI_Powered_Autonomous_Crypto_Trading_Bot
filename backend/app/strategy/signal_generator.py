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
        min_prediction_confidence: Optional[float] = None,
        estimated_cost_hurdle_pct: float = 0.003,  # 0.30% minimum expected profit hurdle (covering 2x fee + 2x slippage)
    ):
        self.min_confidence = (
            min_prediction_confidence
            if min_prediction_confidence is not None
            else getattr(settings, "MIN_PREDICTION_CONFIDENCE", 0.65)
        )
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
        latest_features, meta = FeaturePipeline.get_latest_feature_vector(df_features)

        rsi = float(latest_features.get("rsi_14", 50.0))
        trend_regime = int(latest_features.get("regime_trend", 0))
        close_p = float(df_candles["close"].iloc[-1]) if "close" in df_candles.columns else 0.0
        atr_pct = float(latest_features.get("atr_pct", 0.015))
        atr_14 = float(df_features["atr_14"].iloc[-1]) if "atr_14" in df_features.columns else float(close_p * atr_pct)

        adx = float(df_features["adx_14"].iloc[-1]) if "adx_14" in df_features.columns else 20.0
        plus_di = float(df_features["plus_di_14"].iloc[-1]) if "plus_di_14" in df_features.columns else 0.0
        minus_di = float(df_features["minus_di_14"].iloc[-1]) if "minus_di_14" in df_features.columns else 0.0
        chop = float(df_features["chop_14"].iloc[-1]) if "chop_14" in df_features.columns else 50.0
        mfi = float(df_features["mfi_14"].iloc[-1]) if "mfi_14" in df_features.columns else 50.0
        ch_long = float(df_features["chandelier_long"].iloc[-1]) if "chandelier_long" in df_features.columns else (close_p - 2.5 * atr_14)

        # Append quantitative metrics to reasoning
        reasoning.append(f"ADX (14): {adx:.1f} (Trend Strength: {'Strong' if adx >= 25 else 'Moderate' if adx >= 20 else 'Weak / Chop'})")
        reasoning.append(f"Choppiness Index: {chop:.1f} (Regime: {'Consolidation / Chop' if chop > 61.8 else 'Trending' if chop < 38.2 else 'Neutral'})")
        reasoning.append(f"Money Flow Index (MFI): {mfi:.1f}")

        # 3. Deterministic Quantitative Filter Logic
        # Condition A: Machine learning buy confidence
        is_ml_buy = buy_prob >= self.min_confidence

        # Condition B: Hurdle rate (expected return exceeds transaction costs)
        is_profitable_hurdle = expected_ret > self.cost_hurdle

        # Condition C: Regime filter (avoid severe downtrends unless oversold bounce or strong ML signal)
        ema_ratio = float(latest_features.get("ema_ratio_20_50", 0.0))
        is_trend_acceptable = (
            (trend_regime >= 0)
            or (ema_ratio > -0.003)
            or (rsi < 35.0)
            or (buy_prob >= 0.70)
        )

        # Condition D: Overbought exhaustion guard (RSI < 72 and MFI < 82)
        is_not_overbought = (rsi < 72.0) and (mfi < 82.0)

        # Condition E: Anti-Chop Protection
        # When ADX is very low (< 18) AND Choppiness is very high (> 62), market is dead sideways.
        # Suppress trend breakout buys unless it is a high-probability oversold mean-reversion (RSI < 35)
        is_severe_chop = (adx < 18.0) and (chop > 62.0)
        if is_severe_chop and rsi >= 35.0 and buy_prob < 0.80:
            return {
                "signal": "HOLD / NO TRADE",
                "raw_action": "HOLD",
                "confidence": 0.85,
                "expected_return_pct": 0.0,
                "current_price": close_p,
                "atr": atr_14,
                "adx": adx,
                "chop": chop,
                "mfi": mfi,
                "chandelier_stop": ch_long,
                "reason": f"Anti-Chop Filter: Market in sideways consolidation (ADX {adx:.1f} < 18, CHOP {chop:.1f} > 62). Preserving capital.",
                "reasons_list": reasoning,
            }

        # Calculate composite conviction score for multi-asset ranking (0.0 to 1.0)
        adx_factor = min(adx / 50.0, 1.0)
        mfi_factor = min(mfi / 100.0, 1.0)
        conviction_score = (
            (0.40 * buy_prob)
            + (0.25 * min(expected_ret / 0.02, 1.0))
            + (0.20 * adx_factor)
            + (0.15 * mfi_factor)
        )

        if is_ml_buy and is_profitable_hurdle and is_trend_acceptable and is_not_overbought:
            return {
                "signal": "BUY",
                "raw_action": "BUY",
                "confidence": confidence,
                "conviction_score": round(conviction_score, 4),
                "expected_return_pct": expected_ret * 100.0,
                "current_price": close_p,
                "atr": atr_14,
                "adx": adx,
                "chop": chop,
                "mfi": mfi,
                "chandelier_stop": ch_long,
                "reason": f"ML Buy Prob ({buy_prob * 100:.1f}%) > {self.min_confidence * 100:.1f}%, Expected return exceeds fee hurdle (Conviction: {conviction_score * 100:.1f}%).",
                "reasons_list": reasoning,
            }

        elif sell_prob >= self.min_confidence or (trend_regime == -1 and rsi > 70):
            return {
                "signal": "SELL",
                "raw_action": "SELL",
                "confidence": max(sell_prob, 0.70),
                "conviction_score": 0.0,
                "expected_return_pct": 0.0,
                "current_price": close_p,
                "atr": atr_14,
                "adx": adx,
                "chop": chop,
                "mfi": mfi,
                "chandelier_stop": ch_long,
                "reason": "Bearish setup / Overbought exhaustion detected.",
                "reasons_list": reasoning,
            }

        return {
            "signal": "HOLD / NO TRADE",
            "raw_action": "HOLD",
            "confidence": pred["probabilities"]["hold"],
            "conviction_score": 0.0,
            "expected_return_pct": 0.0,
            "current_price": close_p,
            "atr": atr_14,
            "adx": adx,
            "chop": chop,
            "mfi": mfi,
            "chandelier_stop": ch_long,
            "reason": "Market setup does not meet statistical entry threshold -> Capital Preserved.",
            "reasons_list": reasoning,
        }
