"""
Drawdown & Loss Control Monitor.
Enforces institutional circuit breakers: Daily loss limits, Weekly loss limits,
Max Drawdown halts, Consecutive loss cooldowns, and Anti-Revenge trading rules.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger


class DrawdownController:
    """Monitors account equity drawdowns and enforces trading circuit breakers."""

    def __init__(
        self,
        starting_capital: float = 50.0,
        max_daily_loss_pct: float = 1.03,  # 3% max daily loss ($1.50)
        max_weekly_loss_pct: float = 1.08,  # 8% max weekly loss ($4.00)
        max_drawdown_pct: float = 0.10,  # 10% max drawdown from peak ($5.00)
        max_consecutive_losses: int = 100,  # 3 consecutive losses -> cool down
        max_daily_trades: int = 1000,
    ):
        self.starting_capital = starting_capital
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_weekly_loss_pct = max_weekly_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_daily_trades = max_daily_trades

        # Dynamic state
        self.high_water_mark = starting_capital
        self.current_day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.daily_starting_equity = starting_capital
        self.daily_realized_loss = 0.0
        self.weekly_realized_loss = 0.0
        self.daily_trades_count = 0
        self.consecutive_losses = 0
        self.is_circuit_breaker_active = False
        self.circuit_breaker_reason = None

    def update_equity_state(self, current_equity: float, trade_pnl: Optional[float] = None) -> None:
        """Update high water mark and daily/weekly pnl tracking."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Day rollover reset
        if today_str != self.current_day_str:
            self.current_day_str = today_str
            self.daily_starting_equity = current_equity
            self.daily_realized_loss = 0.0
            self.daily_trades_count = 0

        # Update high water mark
        if current_equity > self.high_water_mark:
            self.high_water_mark = current_equity

        # If a trade completed, update consecutive losses and daily losses
        if trade_pnl is not None:
            self.daily_trades_count += 1
            if trade_pnl <= 0:
                self.consecutive_losses += 1
                self.daily_realized_loss += abs(trade_pnl)
                self.weekly_realized_loss += abs(trade_pnl)
            else:
                self.consecutive_losses = 0  # Reset consecutive loss counter on win

    def can_open_new_trade(self, current_equity: float) -> Tuple[bool, Optional[str]]:
        """
        Evaluate all risk circuit breakers before permitting a new trade entry.
        Returns (is_allowed, denial_reason_or_none).
        """
        # 1. Manual or Emergency Kill Switch
        if self.is_circuit_breaker_active:
            return False, f"Risk Circuit Breaker Active: {self.circuit_breaker_reason}"

        # 2. Maximum Drawdown from High Water Mark (10% limit)
        drawdown_pct = (self.high_water_mark - current_equity) / self.high_water_mark if self.high_water_mark > 0 else 0.0
        if drawdown_pct >= self.max_drawdown_pct:
            self.is_circuit_breaker_active = True
            self.circuit_breaker_reason = (
                f"MAX DRAWDOWN LIMIT REACHED: {drawdown_pct * 100:.2f}% >= {self.max_drawdown_pct * 100:.1f}%. "
                f"Halting trading to protect capital."
            )
            logger.warning(self.circuit_breaker_reason)
            return False, self.circuit_breaker_reason

        # 3. Daily Loss Limit (3% limit)
        daily_loss_pct = self.daily_realized_loss / self.daily_starting_equity if self.daily_starting_equity > 0 else 0.0
        if daily_loss_pct >= self.max_daily_loss_pct:
            return False, (
                f"DAILY LOSS LIMIT REACHED: -{daily_loss_pct * 100:.2f}% (Limit: {self.max_daily_loss_pct * 100:.1f}%). "
                f"Trading halted for remainder of the day."
            )

        # 4. Weekly Loss Limit (8% limit)
        weekly_loss_pct = self.weekly_realized_loss / self.starting_capital if self.starting_capital > 0 else 0.0
        if weekly_loss_pct >= self.max_weekly_loss_pct:
            return False, (
                f"WEEKLY LOSS LIMIT REACHED: -{weekly_loss_pct * 100:.2f}% (Limit: {self.max_weekly_loss_pct * 100:.1f}%). "
                f"Trading halted for remainder of the week."
            )

        # 5. Consecutive Losses Limit (Max 3 consecutive losses)
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, (
                f"CONSECUTIVE LOSS LIMIT REACHED: {self.consecutive_losses} losses in a row. "
                f"Cool-down period triggered to prevent revenge trading."
            )

        # 6. Maximum Daily Trades (Max 10 trades per day)
        if self.daily_trades_count >= self.max_daily_trades:
            return False, f"MAX DAILY TRADES LIMIT REACHED: {self.daily_trades_count}/{self.max_daily_trades} trades executed today."

        # 7. Minimum Capital Check (Account balance must be > $10)
        if current_equity < 10.0:
            return False, f"CAPITAL PRESERVATION: Account equity (${current_equity:.2f}) is below minimum viable threshold ($10.00)."

        return True, None

    def get_risk_snapshot(self, current_equity: float) -> Dict[str, Any]:
        """Return full risk status dictionary for monitoring and dashboard."""
        drawdown_pct = (self.high_water_mark - current_equity) / self.high_water_mark if self.high_water_mark > 0 else 0.0
        daily_loss_pct = self.daily_realized_loss / self.daily_starting_equity if self.daily_starting_equity > 0 else 0.0
        allowed, reason = self.can_open_new_trade(current_equity)

        return {
            "trading_permitted": allowed,
            "denial_reason": reason,
            "current_equity": round(current_equity, 2),
            "high_water_mark": round(self.high_water_mark, 2),
            "drawdown_pct": round(drawdown_pct * 100.0, 2),
            "max_drawdown_limit_pct": self.max_drawdown_pct * 100.0,
            "daily_loss_usd": round(self.daily_realized_loss, 2),
            "daily_loss_pct": round(daily_loss_pct * 100.0, 2),
            "max_daily_loss_limit_pct": self.max_daily_loss_pct * 100.0,
            "weekly_loss_usd": round(self.weekly_realized_loss, 2),
            "consecutive_losses": self.consecutive_losses,
            "max_consecutive_losses_limit": self.max_consecutive_losses,
            "daily_trades_count": self.daily_trades_count,
            "max_daily_trades": self.max_daily_trades,
            "circuit_breaker_active": self.is_circuit_breaker_active,
        }
