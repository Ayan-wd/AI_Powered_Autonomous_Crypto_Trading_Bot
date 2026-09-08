"""
Master Risk Management Gateway.
Validates all proposed orders against capital limits, position sizing constraints,
and circuit breakers before execution authorization.
"""

from typing import Any, Dict, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.risk.drawdown_control import DrawdownController
from backend.app.risk.position_sizing import PositionSizer


class RiskManager:
    """Central risk authority ensuring capital preservation is prioritized over trading volume."""

    def __init__(
        self,
        starting_capital: Optional[float] = None,
        max_risk_per_trade: Optional[float] = None,
        max_position_size_usd: Optional[float] = None,
        max_daily_loss_pct: Optional[float] = None,
        max_drawdown_pct: Optional[float] = None,
    ):
        self.capital = starting_capital or settings.STARTING_CAPITAL
        self.position_sizer = PositionSizer(
            max_risk_pct=max_risk_per_trade or settings.MAX_RISK_PER_TRADE_PCT,
            max_position_size_usd=max_position_size_usd or settings.MAX_POSITION_SIZE_USD,
        )
        self.drawdown_controller = DrawdownController(
            starting_capital=self.capital,
            max_daily_loss_pct=max_daily_loss_pct or settings.MAX_DAILY_LOSS_PCT,
            max_drawdown_pct=max_drawdown_pct or settings.MAX_DRAWDOWN_PCT,
            max_consecutive_losses=settings.MAX_CONSECUTIVE_LOSSES,
            max_daily_trades=settings.MAX_DAILY_TRADES,
        )

    def evaluate_order(
        self,
        account_equity: float,
        current_price: float,
        side: str,
        stop_loss_price: Optional[float] = None,
        atr: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Evaluate if a proposed order passes all risk filters, calculate position size,
        and establish deterministic Stop Loss and Take Profit levels.
        """
        # 1. Check circuit breakers
        can_trade, denial_reason = self.drawdown_controller.can_open_new_trade(account_equity)
        if not can_trade:
            logger.warning(f"Risk Manager Denied Order: {denial_reason}")
            return {
                "approved": False,
                "reason": denial_reason,
                "quantity": 0.0,
                "position_value_usd": 0.0,
                "stop_loss": None,
                "take_profit": None,
            }

        # 2. Establish and validate Stop Loss price
        if stop_loss_price is None or stop_loss_price <= 0:
            if side == "BUY":
                if atr > 0:
                    stop_loss_price = current_price - (1.5 * atr)
                else:
                    stop_loss_price = current_price * (1.0 - settings.DEFAULT_STOP_LOSS_PCT)
            else:
                if atr > 0:
                    stop_loss_price = current_price + (1.5 * atr)
                else:
                    stop_loss_price = current_price * (1.0 + settings.DEFAULT_STOP_LOSS_PCT)

        # STRICT DIRECTIONAL INVARIANT CHECKS:
        if side == "BUY":
            if stop_loss_price >= current_price:
                logger.error(
                    f"CRITICAL REJECTION: Long Stop-Loss (${stop_loss_price:.2f}) is on wrong side of entry (${current_price:.2f})."
                )
                return {
                    "approved": False,
                    "reason": f"DIRECTIONAL INVARIANT VIOLATION: Long stop-loss (${stop_loss_price:.2f}) must be strictly below entry price (${current_price:.2f}).",
                    "quantity": 0.0,
                    "position_value_usd": 0.0,
                    "stop_loss": None,
                    "take_profit": None,
                }
        elif side == "SELL":
            if stop_loss_price <= current_price:
                logger.error(
                    f"CRITICAL REJECTION: Short Stop-Loss (${stop_loss_price:.2f}) is on wrong side of entry (${current_price:.2f})."
                )
                return {
                    "approved": False,
                    "reason": f"DIRECTIONAL INVARIANT VIOLATION: Short stop-loss (${stop_loss_price:.2f}) must be strictly above entry price (${current_price:.2f}).",
                    "quantity": 0.0,
                    "position_value_usd": 0.0,
                    "stop_loss": None,
                    "take_profit": None,
                }

        # 3. Establish Take Profit price (2:1 reward/risk ratio)
        risk_distance = abs(current_price - stop_loss_price)
        if side == "BUY":
            take_profit_price = current_price + (2.0 * risk_distance)
        else:
            take_profit_price = current_price - (2.0 * risk_distance)

        if side == "BUY" and take_profit_price <= current_price:
            return {
                "approved": False,
                "reason": "Take-profit price must be strictly greater than entry price for Long.",
                "quantity": 0.0,
                "position_value_usd": 0.0,
                "stop_loss": None,
                "take_profit": None,
            }

        # 4. Calculate safe position size
        sizing = self.position_sizer.calculate_position_size(
            account_equity=account_equity,
            current_price=current_price,
            stop_loss_price=stop_loss_price,
            atr=atr,
        )

        if sizing["quantity"] <= 0 or sizing["position_value_usd"] <= 0:
            return {
                "approved": False,
                "reason": "Calculated position quantity is zero or exceeds capital limits.",
                "quantity": 0.0,
                "position_value_usd": 0.0,
                "stop_loss": None,
                "take_profit": None,
            }

        return {
            "approved": True,
            "reason": "Order passed all quantitative risk limits and sizing checks.",
            "quantity": sizing["quantity"],
            "position_value_usd": sizing["position_value_usd"],
            "risk_amount_usd": sizing["risk_amount_usd"],
            "entry_price": current_price,
            "stop_loss": round(stop_loss_price, 2),
            "take_profit": round(take_profit_price, 2),
            "risk_reward_ratio": round((take_profit_price - current_price) / risk_distance, 2) if risk_distance > 0 else 2.0,
        }

    def record_trade_completion(self, current_equity: float, pnl: float) -> None:
        """Inform drawdown controller that a trade has closed with a specific PnL."""
        self.drawdown_controller.update_equity_state(current_equity, trade_pnl=pnl)


# Global singleton instance
risk_manager = RiskManager()
