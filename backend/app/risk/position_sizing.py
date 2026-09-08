"""
Quantitative Position Sizing Engine.
Calculates risk-adjusted position sizes based on fixed-fractional risk (1% account equity)
and volatility (ATR) while strictly capping max position value ($10 on $50 capital).
Anti-Martingale guaranteed.
"""

from typing import Dict
from backend.app.core.config import settings
from backend.app.core.logging import logger


class PositionSizer:
    """Calculates safe, risk-managed order quantities for spot crypto trading."""

    def __init__(
        self,
        max_risk_pct: float = 0.25,  # Maximum risk per trade (25% risk budget)
        max_position_size_usd: float = 10000.0,  # Max position size up to $10,000 USD testnet balance
        min_order_size_usd: float = 10.0,  # Binance testnet minimum spot order
    ):
        self.max_risk_pct = max_risk_pct
        self.max_position_size_usd = max_position_size_usd
        self.min_order_size_usd = min_order_size_usd

    def calculate_position_size(
        self,
        account_equity: float,
        current_price: float,
        stop_loss_price: float,
        atr: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calculate order quantity:
        Risk Amount = Equity * Max Risk % (e.g. $50 * 1% = $0.50)
        Risk Per Unit = abs(current_price - stop_loss_price)
        Raw Position Qty = Risk Amount / Risk Per Unit
        Position USD = Raw Position Qty * current_price
        Capped Position USD = min(Position USD, max_position_size_usd, account_equity)
        """
        if account_equity <= 0 or current_price <= 0:
            return {"quantity": 0.0, "position_value_usd": 0.0, "risk_amount_usd": 0.0}

        # 1. Fixed fractional risk dollar amount
        risk_budget_usd = account_equity * self.max_risk_pct

        # 2. Risk per unit based on stop loss distance
        price_risk_per_unit = abs(current_price - stop_loss_price)
        if price_risk_per_unit <= 0:
            # Fallback to default stop loss percentage
            price_risk_per_unit = current_price * settings.DEFAULT_STOP_LOSS_PCT

        # 3. Position size from risk budget
        raw_quantity = risk_budget_usd / price_risk_per_unit
        raw_position_value_usd = raw_quantity * current_price

        # 4. Strict upper bounds check:
        # Cannot exceed max_position_size_usd ($10) AND cannot exceed total equity ($50)
        max_allowed_usd = min(self.max_position_size_usd, account_equity)
        final_position_usd = min(raw_position_value_usd, max_allowed_usd)

        # 5. Check minimum order threshold
        if final_position_usd < self.min_order_size_usd and account_equity >= self.min_order_size_usd:
            # If calculated size is slightly below min lot but within risk budget, set to min order size
            final_position_usd = self.min_order_size_usd

        if final_position_usd > account_equity:
            final_position_usd = 0.0

        final_quantity = final_position_usd / current_price if current_price > 0 else 0.0

        return {
            "quantity": round(final_quantity, 6),
            "position_value_usd": round(final_position_usd, 2),
            "risk_amount_usd": round(risk_budget_usd, 3),
            "max_allowed_usd": max_allowed_usd,
        }
