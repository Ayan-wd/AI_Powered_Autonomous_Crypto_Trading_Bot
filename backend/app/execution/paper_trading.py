"""
Paper Trading Exchange Simulator.
High-fidelity simulated order execution environment with realistic transaction fees (0.10%),
slippage modeling (0.05%), position tracking, and intrabar Stop-Loss / Take-Profit trigger evaluation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from backend.app.core.config import settings
from backend.app.core.logging import logger


class PaperPosition:
    """Represents an active paper trading open position."""

    def __init__(
        self,
        trade_id: str,
        symbol: str,
        side: str,  # "BUY" (long)
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        entry_time: Optional[datetime] = None,
        model_probability: Optional[float] = None,
        strategy_reason: Optional[str] = None,
        explanation_json: Optional[str] = None,
    ):
        self.trade_id = trade_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = entry_time or datetime.now(timezone.utc)
        self.model_probability = model_probability
        self.strategy_reason = strategy_reason
        self.explanation_json = explanation_json
        self.highest_price = entry_price
        self.current_price = entry_price

    def update_mark_price(self, mark_price: float) -> None:
        """Update current mark price and track highest price for trailing logic."""
        self.current_price = mark_price
        if mark_price > self.highest_price:
            self.highest_price = mark_price

    @property
    def position_value_usd(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis_usd(self) -> float:
        return self.quantity * self.entry_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": round(self.entry_price, 2),
            "current_price": round(self.current_price, 2),
            "quantity": round(self.quantity, 6),
            "position_value_usd": round(self.position_value_usd, 2),
            "cost_basis_usd": round(self.cost_basis_usd, 2),
            "unrealized_pnl_usd": round(self.unrealized_pnl, 2),
            "unrealized_pnl_pct": round(self.unrealized_pnl_pct * 100.0, 2),
            "stop_loss": round(self.stop_loss, 2) if self.stop_loss else None,
            "take_profit": round(self.take_profit, 2) if self.take_profit else None,
            "highest_price": round(self.highest_price, 2),
            "entry_time": self.entry_time.isoformat(),
            "model_probability": self.model_probability,
            "strategy_reason": self.strategy_reason,
        }


class PaperExchangeSimulator:
    """Simulates spot exchange order matching, balances, fees, and SL/TP triggers."""

    def __init__(
        self,
        starting_capital: float = 50.0,
        fee_rate: float = 0.001,  # 0.10% Binance spot standard
        slippage_rate: float = 0.0005,  # 0.05% realistic market slippage
    ):
        self.starting_capital = starting_capital
        self.usdt_balance = starting_capital
        self.base_balance = 0.0  # BTC or other crypto asset balance
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.active_position: Optional[PaperPosition] = None
        self.realized_pnl_total = 0.0
        self.total_fees_paid = 0.0

    def reset_account(self, starting_capital: Optional[float] = None) -> None:
        """Reset paper account to initial clean state."""
        cap = starting_capital or self.starting_capital
        self.starting_capital = cap
        self.usdt_balance = cap
        self.base_balance = 0.0
        self.active_position = None
        self.realized_pnl_total = 0.0
        self.total_fees_paid = 0.0
        logger.info(f"Paper Trading Account reset to ${cap:.2f} USDT.")

    def get_total_equity(self, current_price: Optional[float] = None) -> float:
        """Calculate total account equity (USDT balance + open position value)."""
        if self.active_position:
            price = current_price or self.active_position.current_price
            return self.usdt_balance + (self.active_position.quantity * price)
        return self.usdt_balance

    def execute_market_buy(
        self,
        symbol: str,
        price: float,
        position_size_usd: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        model_probability: Optional[float] = None,
        strategy_reason: Optional[str] = None,
        explanation_json: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute simulated market BUY order.
        Applies upward slippage on entry and deducts Binance spot fee.
        """
        if self.active_position is not None:
            return {
                "status": "REJECTED",
                "reason": "Position already open. Single concurrent position enforced.",
            }

        if position_size_usd > self.usdt_balance:
            position_size_usd = self.usdt_balance

        if position_size_usd < 5.0:
            return {
                "status": "REJECTED",
                "reason": f"Position size (${position_size_usd:.2f}) below minimum order lot ($5.00).",
            }

        # Apply slippage (buy price slightly higher)
        execution_price = price * (1.0 + self.slippage_rate)
        fee_usd = position_size_usd * self.fee_rate
        net_capital = position_size_usd - fee_usd
        quantity = net_capital / execution_price

        # Update wallet balance
        self.usdt_balance -= position_size_usd
        self.total_fees_paid += fee_usd

        trade_id = f"paper_{uuid.uuid4().hex[:12]}"
        client_order_id = f"ord_{uuid.uuid4().hex[:10]}"

        # Create active paper position
        self.active_position = PaperPosition(
            trade_id=trade_id,
            symbol=symbol,
            side="BUY",
            entry_price=execution_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(timezone.utc),
            model_probability=model_probability,
            strategy_reason=strategy_reason,
            explanation_json=explanation_json,
        )

        logger.info(
            f"📈 [PAPER BUY] {symbol} Qty: {quantity:.6f} @ ${execution_price:.2f} "
            f"(Cost: ${position_size_usd:.2f}, Fee: ${fee_usd:.4f}, SL: ${stop_loss or 0:.2f}, TP: ${take_profit or 0:.2f})"
        )

        return {
            "status": "FILLED",
            "trade_id": trade_id,
            "client_order_id": client_order_id,
            "symbol": symbol,
            "side": "BUY",
            "entry_price": execution_price,
            "quantity": quantity,
            "fee_usd": fee_usd,
            "slippage_usd": position_size_usd * self.slippage_rate,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "created_at": self.active_position.entry_time.isoformat(),
        }

    def execute_market_sell(
        self,
        exit_price: float,
        exit_reason: str = "SIGNAL_EXIT",
    ) -> Optional[Dict[str, Any]]:
        """
        Execute simulated market SELL to close the active position.
        Applies downward slippage and deducts spot exit fee.
        """
        if self.active_position is None:
            return None

        pos = self.active_position
        execution_price = exit_price * (1.0 - self.slippage_rate)
        gross_return_usd = pos.quantity * execution_price
        exit_fee_usd = gross_return_usd * self.fee_rate
        net_return_usd = gross_return_usd - exit_fee_usd

        # Calculate PnL
        pnl_usd = net_return_usd - pos.cost_basis_usd
        pnl_pct = (execution_price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0.0

        # Update wallet balance
        self.usdt_balance += net_return_usd
        self.realized_pnl_total += pnl_usd
        self.total_fees_paid += exit_fee_usd

        exit_time = datetime.now(timezone.utc)
        trade_summary = {
            "status": "CLOSED",
            "trade_id": pos.trade_id,
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": execution_price,
            "quantity": pos.quantity,
            "entry_time": pos.entry_time,
            "exit_time": exit_time,
            "pnl": pnl_usd,
            "pnl_pct": pnl_pct,
            "fees": exit_fee_usd,
            "slippage": pos.quantity * exit_price * self.slippage_rate,
            "stop_loss": pos.stop_loss,
            "take_profit": pos.take_profit,
            "model_probability": pos.model_probability,
            "strategy_reason": f"{pos.strategy_reason or 'STRATEGY'} -> Closed: {exit_reason}",
            "explanation_json": pos.explanation_json,
            "exit_reason": exit_reason,
        }

        self.active_position = None
        logger.info(
            f"📉 [PAPER SELL / CLOSE] {pos.symbol} Exit @ ${execution_price:.2f} | "
            f"PnL: {'+' if pnl_usd >= 0 else ''}${pnl_usd:.2f} ({pnl_pct * 100:.2f}%) | "
            f"Reason: {exit_reason}"
        )
        return trade_summary

    def check_intrabar_triggers(
        self,
        current_price: float,
        candle_high: Optional[float] = None,
        candle_low: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if active position hit Stop-Loss or Take-Profit thresholds.
        Returns closed trade summary dictionary if triggered, else None.
        """
        if self.active_position is None:
            return None

        pos = self.active_position
        pos.update_mark_price(current_price)

        high_val = candle_high if candle_high is not None else current_price
        low_val = candle_low if candle_low is not None else current_price

        # Check Stop Loss Trigger
        if pos.stop_loss is not None and low_val <= pos.stop_loss:
            return self.execute_market_sell(exit_price=pos.stop_loss, exit_reason="STOP_LOSS")

        # Check Take Profit Trigger
        if pos.take_profit is not None and high_val >= pos.take_profit:
            return self.execute_market_sell(exit_price=pos.take_profit, exit_reason="TAKE_PROFIT")

        return None
