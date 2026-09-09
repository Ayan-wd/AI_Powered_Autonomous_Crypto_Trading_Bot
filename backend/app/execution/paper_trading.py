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
        cost_basis_usd: float,
        entry_fee_usd: float = 0.0,
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
        self._cost_basis_usd = cost_basis_usd
        self.entry_fee_usd = entry_fee_usd
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = entry_time or datetime.now(timezone.utc)
        self.model_probability = model_probability
        self.strategy_reason = strategy_reason
        self.explanation_json = explanation_json
        self.highest_price = entry_price
        self.current_price = entry_price
        self.initial_risk = abs(entry_price - stop_loss) if stop_loss else entry_price * 0.015
        self.breakeven_triggered = False
        self.trailing_stop_active = False

    def update_mark_price(self, mark_price: float) -> None:
        """Update current mark price and track highest price for trailing logic."""
        self.current_price = mark_price
        if mark_price > self.highest_price:
            self.highest_price = mark_price

    def update_trailing_and_breakeven(self, current_price: float, atr: float = 0.0) -> Optional[str]:
        """
        Adaptive Stop Management:
        1. Breakeven Lock: When price reaches >= entry + 1.0R (or +0.60%), ratchet Stop-Loss to entry + 0.20%
           (guaranteeing zero capital risk and covering round-trip exchange fees).
        2. Chandelier Trailing Stop: Once in profit, trail Stop-Loss at highest_price - (1.5 * ATR).
           Stop-Loss monotonically ratchets UP only, never down.
        """
        if self.side != "BUY" or self.stop_loss is None:
            return None

        event: Optional[str] = None
        r_multiple = (self.highest_price - self.entry_price) / self.initial_risk if self.initial_risk > 0 else 0.0

        # 1. Breakeven Lock at +1.0R gain
        breakeven_target = self.entry_price * 1.002  # +0.20% to cover round-trip exchange fees
        if not self.breakeven_triggered and r_multiple >= 1.0:
            if breakeven_target > self.stop_loss:
                self.stop_loss = breakeven_target
                self.breakeven_triggered = True
                event = f"BREAKEVEN_LOCK (Price gained +{r_multiple:.2f}R | SL locked to ${self.stop_loss:.2f})"
                logger.info(f"[{self.symbol}] {event}")

        # 2. Chandelier / ATR Trailing Stop (requires positive ATR)
        if atr > 0.0:
            chandelier_trail = self.highest_price - (1.5 * atr)
            if chandelier_trail > self.stop_loss and chandelier_trail > self.entry_price:
                self.stop_loss = chandelier_trail
                self.trailing_stop_active = True
                event = f"TRAILING_STOP_RATCHET (High ${self.highest_price:.2f} | SL ratcheted to ${self.stop_loss:.2f})"
                logger.info(f"[{self.symbol}] {event}")

        return event

    @property
    def position_value_usd(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis_usd(self) -> float:
        return self._cost_basis_usd

    @property
    def unrealized_pnl(self) -> float:
        return (self.position_value_usd - self._cost_basis_usd)

    @property
    def unrealized_pnl_pct(self) -> float:
        return (self.position_value_usd - self._cost_basis_usd) / self._cost_basis_usd if self._cost_basis_usd > 0 else 0.0

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
            "breakeven_triggered": self.breakeven_triggered,
            "trailing_stop_active": self.trailing_stop_active,
        }


class PaperExchangeSimulator:
    """Simulates spot exchange order matching, balances, fees, and SL/TP triggers."""

    def __init__(
        self,
        starting_capital: float = 10000.0,
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
        ask_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute simulated market BUY order.
        Uses ask_price when available (real bid/ask spread), applies upward slippage,
        and deducts Binance spot fee.
        Enforces strict directional Stop-Loss integrity: stop_loss < execution_price.
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

        base_buy_price = ask_price if (ask_price is not None and ask_price > 0) else price
        execution_price = base_buy_price * (1.0 + self.slippage_rate)

        # Invariant check: Stop-Loss MUST be strictly below execution price for a Long
        if stop_loss is not None and stop_loss >= execution_price:
            logger.error(
                f"REJECTED BUY ORDER: Inverted Stop-Loss. SL=${stop_loss:.2f} >= Entry=${execution_price:.2f}"
            )
            return {
                "status": "REJECTED",
                "reason": f"DIRECTIONAL INVARIANT VIOLATION: Stop-loss (${stop_loss:.2f}) must be < Entry (${execution_price:.2f}).",
            }

        if take_profit is not None and take_profit <= execution_price:
            logger.error(
                f"REJECTED BUY ORDER: Inverted Take-Profit. TP=${take_profit:.2f} <= Entry=${execution_price:.2f}"
            )
            return {
                "status": "REJECTED",
                "reason": f"DIRECTIONAL INVARIANT VIOLATION: Take-profit (${take_profit:.2f}) must be > Entry (${execution_price:.2f}).",
            }

        fee_usd = position_size_usd * self.fee_rate
        net_capital = position_size_usd - fee_usd
        quantity = net_capital / execution_price

        # Total cash invested is position_size_usd (net_capital + fee_usd)
        self.usdt_balance -= position_size_usd
        self.total_fees_paid += fee_usd

        trade_id = f"paper_{uuid.uuid4().hex[:12]}"
        client_order_id = f"ord_{uuid.uuid4().hex[:10]}"

        # Create active paper position with full cost basis tracked
        self.active_position = PaperPosition(
            trade_id=trade_id,
            symbol=symbol,
            side="BUY",
            entry_price=execution_price,
            quantity=quantity,
            cost_basis_usd=position_size_usd,
            entry_fee_usd=fee_usd,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(timezone.utc),
            model_probability=model_probability,
            strategy_reason=strategy_reason,
            explanation_json=explanation_json,
        )

        logger.info(
            f"[PAPER BUY] {symbol} Qty: {quantity:.6f} @ ${execution_price:.2f} "
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
        bid_price: Optional[float] = None,
        adverse_slippage_pct: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute simulated market SELL to close the active position.
        Uses bid_price when available (real bid/ask spread), applies conservative slippage,
        and deducts spot exit fee.
        Includes full round-trip fee accounting (entry fee + exit fee) in trade PnL.
        Enforces impossible-profit prevention on Stop-Loss exits.
        """
        if self.active_position is None:
            return None

        pos = self.active_position
        base_sell_price = bid_price if (bid_price is not None and bid_price > 0) else exit_price

        # Apply conservative adverse slippage
        slip_rate = adverse_slippage_pct if adverse_slippage_pct is not None else self.slippage_rate
        execution_price = base_sell_price * (1.0 - slip_rate)

        # IMPOSSIBLE-PRICE GUARD on Stop-Loss:
        # A Long position stopped out can NEVER execute at a price higher than pos.stop_loss
        # For initial stop loss (not ratcheted by breakeven/trailing), cannot execute above entry.
        if pos.side == "BUY" and exit_reason == "STOP_LOSS":
            if pos.stop_loss is not None:
                max_allowed_sl_exit = pos.stop_loss * (1.0 - slip_rate)
                execution_price = min(execution_price, max_allowed_sl_exit)
            if not pos.breakeven_triggered and not pos.trailing_stop_active:
                if execution_price >= pos.entry_price:
                    execution_price = pos.entry_price * (1.0 - max(slip_rate, 0.001))

        gross_return_usd = pos.quantity * execution_price
        exit_fee_usd = gross_return_usd * self.fee_rate
        net_return_usd = gross_return_usd - exit_fee_usd

        # Full round-trip PnL calculation:
        # PnL = Net Cash Returned - Total Cash Invested (which included entry fee)
        # Identically: (Gross Return - Exit Fee) - (Quantity * Entry Price + Entry Fee)
        pnl_usd = net_return_usd - pos.cost_basis_usd
        total_fees_usd = pos.entry_fee_usd + exit_fee_usd
        pnl_pct = (pnl_usd / pos.cost_basis_usd) if pos.cost_basis_usd > 0 else 0.0

        # Update wallet balance and aggregate accounting
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
            "fees": total_fees_usd,
            "entry_fee": pos.entry_fee_usd,
            "exit_fee": exit_fee_usd,
            "slippage": pos.quantity * exit_price * slip_rate,
            "stop_loss": pos.stop_loss,
            "take_profit": pos.take_profit,
            "model_probability": pos.model_probability,
            "strategy_reason": f"{pos.strategy_reason or 'STRATEGY'} -> Closed: {exit_reason}",
            "explanation_json": pos.explanation_json,
            "exit_reason": exit_reason,
        }

        self.active_position = None
        logger.info(
            f"[PAPER SELL / CLOSE] {pos.symbol} Exit @ ${execution_price:.2f} | "
            f"PnL: {'+' if pnl_usd >= 0 else ''}${pnl_usd:.2f} ({pnl_pct * 100:.2f}%) | "
            f"Fees: ${total_fees_usd:.4f} | Reason: {exit_reason}"
        )
        return trade_summary

    def check_intrabar_triggers(
        self,
        current_price: float,
        candle_high: Optional[float] = None,
        candle_low: Optional[float] = None,
        bid_price: Optional[float] = None,
        ask_price: Optional[float] = None,
        atr: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if active position hit Stop-Loss or Take-Profit thresholds.
        Evaluates intrabar price extremes conservatively with adverse slippage.
        Dynamically applies Breakeven Lock (+1.0R) and Chandelier ATR Trailing Stop.
        """
        if self.active_position is None:
            return None

        pos = self.active_position
        pos.update_mark_price(current_price)
        pos.update_trailing_and_breakeven(current_price, atr=atr)

        high_val = candle_high if candle_high is not None else current_price
        low_val = candle_low if candle_low is not None else current_price

        # 1. Check Take Profit Trigger for LONG position
        if pos.side == "BUY" and pos.take_profit is not None:
            if high_val >= pos.take_profit or current_price >= pos.take_profit:
                return self.execute_market_sell(
                    exit_price=pos.take_profit,
                    exit_reason="TAKE_PROFIT",
                    bid_price=bid_price,
                    adverse_slippage_pct=self.slippage_rate,
                )

        # 2. Check Stop Loss Trigger for LONG position
        if pos.side == "BUY" and pos.stop_loss is not None:
            if low_val <= pos.stop_loss or current_price <= pos.stop_loss:
                # Conservative fill: cannot assume fill at exact stop price if market breached deeper
                breached_price = min(pos.stop_loss, low_val, current_price)
                return self.execute_market_sell(
                    exit_price=breached_price,
                    exit_reason="STOP_LOSS",
                    bid_price=bid_price,
                    adverse_slippage_pct=max(self.slippage_rate, 0.001),  # At least 0.1% adverse slippage on SL
                )

        return None
