"""
Deterministic Strategy Decision Engine.
Coordinates candidate signals, active position tracking, and Risk Manager authorization
to emit final execution decisions: BUY (with stop/target), SELL (exit), or HOLD.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.risk.risk_manager import RiskManager, risk_manager
from backend.app.strategy.signal_generator import SignalGenerator


class StrategyDecisionEngine:
    """Master Decision Engine governing entry and exit rules."""

    def __init__(
        self,
        signal_generator: Optional[SignalGenerator] = None,
        risk_gateway: Optional[RiskManager] = None,
    ):
        self.signal_gen = signal_generator or SignalGenerator()
        self.risk_mgr = risk_gateway or risk_manager

    def evaluate_decision(
        self,
        df_candles: pd.DataFrame,
        account_equity: float,
        current_open_position: Optional[Dict[str, Any]] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate full trading system: Signal -> Risk Checks -> Sizing -> Final Order Decision.
        """
        raw_signal = self.signal_gen.generate_signal(df_candles)
        action = raw_signal["raw_action"]
        current_price = raw_signal.get("current_price", 0.0)
        atr = raw_signal.get("atr", 0.0)
        target_symbol = symbol or (current_open_position.get("symbol") if current_open_position else None) or settings.TRADING_SYMBOL

        # 1. Evaluate Exit Conditions if a position is currently open
        if current_open_position:
            entry_price = float(current_open_position.get("entry_price", current_price))
            stop_loss = float(current_open_position.get("stop_loss", entry_price * 0.985))
            take_profit = float(current_open_position.get("take_profit", entry_price * 1.03))

            # Stop loss hit
            if current_price <= stop_loss:
                return {
                    "action": "SELL",
                    "reason": f"STOP LOSS HIT: Price ${current_price:.2f} <= Stop ${stop_loss:.2f}",
                    "confidence": 1.0,
                    "order_details": {"type": "MARKET", "exit_reason": "STOP_LOSS"},
                    "numerical_explanation": raw_signal["reasons_list"],
                }

            # Take profit hit
            if current_price >= take_profit:
                return {
                    "action": "SELL",
                    "reason": f"TAKE PROFIT HIT: Price ${current_price:.2f} >= Target ${take_profit:.2f}",
                    "confidence": 1.0,
                    "order_details": {"type": "MARKET", "exit_reason": "TAKE_PROFIT"},
                    "numerical_explanation": raw_signal["reasons_list"],
                }

            # Strategy exit signal
            if action == "SELL":
                return {
                    "action": "SELL",
                    "reason": f"STRATEGY REVERSAL: {raw_signal['reason']}",
                    "confidence": raw_signal["confidence"],
                    "order_details": {"type": "MARKET", "exit_reason": "SIGNAL_EXIT"},
                    "numerical_explanation": raw_signal["reasons_list"],
                }

            # Otherwise maintain current position
            pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
            return {
                "action": "HOLD",
                "reason": f"Position active (P/L: {pnl_pct:+.2f}%). Trailing within risk corridors.",
                "confidence": 0.80,
                "order_details": None,
                "numerical_explanation": raw_signal["reasons_list"],
            }

        # 2. Evaluate New Entry Conditions (No position currently open)
        if action == "BUY":
            # Pass through master Risk Manager
            risk_eval = self.risk_mgr.evaluate_order(
                account_equity=account_equity,
                current_price=current_price,
                side="BUY",
                atr=atr,
            )

            if risk_eval["approved"]:
                return {
                    "action": "BUY",
                    "reason": raw_signal["reason"],
                    "confidence": raw_signal["confidence"],
                    "order_details": {
                        "symbol": target_symbol,
                        "side": "BUY",
                        "type": "MARKET",
                        "quantity": risk_eval["quantity"],
                        "position_size_usd": risk_eval["position_value_usd"],
                        "position_value_usd": risk_eval["position_value_usd"],
                        "entry_price": current_price,
                        "stop_loss": risk_eval["stop_loss"],
                        "take_profit": risk_eval["take_profit"],
                        "risk_reward_ratio": risk_eval["risk_reward_ratio"],
                    },
                    "numerical_explanation": raw_signal["reasons_list"],
                }
            else:
                # Risk manager rejected order -> Default to HOLD
                return {
                    "action": "HOLD",
                    "reason": f"BUY Signal Suppressed by Risk Gateway: {risk_eval['reason']}",
                    "confidence": 0.90,
                    "order_details": None,
                    "numerical_explanation": raw_signal["reasons_list"],
                }

        # Default fallback is always HOLD
        return {
            "action": "HOLD",
            "reason": raw_signal["reason"],
            "confidence": raw_signal["confidence"],
            "order_details": None,
            "numerical_explanation": raw_signal["reasons_list"],
        }


# Global singleton instance
strategy_engine = StrategyDecisionEngine()
