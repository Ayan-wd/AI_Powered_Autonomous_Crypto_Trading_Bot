"""
Continuous Autonomous Trading Bot Engine.
Asynchronous execution loop that processes live market ticks, evaluates multi-factor strategy signals,
enforces institutional risk rules, and automatically executes paper or live orders.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import async_session_factory
from backend.app.database.models import EquitySnapshot
from backend.app.database.repositories import EquityRepository, LogRepository
from backend.app.execution.order_manager import order_manager
from backend.app.risk.risk_manager import risk_manager
from backend.app.strategy.strategy_engine import strategy_engine


class TradingBotEngine:
    """Autonomous trading bot execution daemon."""

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "15m",
        tick_interval_sec: float = 5.0,
    ):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.tick_interval_sec = tick_interval_sec
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.market_engine = MarketDataEngine()
        self.last_decision: Dict[str, Any] = {
            "action": "HOLD / NO TRADE",
            "reason": "Bot initialized. Awaiting market evaluation.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.last_candle_timestamp: Optional[datetime] = None
        self.iteration_count = 0

    async def start(self) -> Dict[str, Any]:
        """Start the background autonomous trading loop."""
        if self.is_running:
            return {"status": "ALREADY_RUNNING", "message": "Bot is already running."}

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"🚀 [TRADING BOT STARTED] Tracking {self.symbol} ({self.timeframe}) in {settings.TRADING_MODE} mode.")
        return {
            "status": "STARTED",
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "mode": settings.TRADING_MODE,
        }

    async def stop(self) -> Dict[str, Any]:
        """Stop the autonomous trading loop."""
        if not self.is_running:
            return {"status": "NOT_RUNNING", "message": "Bot is not running."}

        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("🛑 [TRADING BOT STOPPED]")
        return {"status": "STOPPED", "message": "Bot background execution halted."}

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status snapshot of the bot."""
        pos = order_manager.get_active_position()
        balances = order_manager.get_account_balances()
        risk_snap = risk_manager.drawdown_controller.get_risk_snapshot(balances["total_equity"])

        return {
            "is_running": self.is_running,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "mode": settings.TRADING_MODE,
            "iteration_count": self.iteration_count,
            "active_position": pos,
            "wallet": balances,
            "risk_snapshot": risk_snap,
            "last_decision": self.last_decision,
        }

    async def _run_loop(self) -> None:
        """Core asynchronous background evaluation loop."""
        logger.info(f"Background trading loop active for {self.symbol}...")
        while self.is_running:
            try:
                self.iteration_count += 1
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trading bot tick loop: {e}", exc_info=True)

            await asyncio.sleep(self.tick_interval_sec)

    async def _tick(self) -> None:
        """Execute one evaluation tick."""
        async with async_session_factory() as session:
            # 1. Fetch current price
            ticker = await self.market_engine.get_live_ticker(self.symbol)
            current_price = ticker.price

            # 2. Evaluate active position Stop-Loss / Take-Profit triggers
            sl_tp_closed = await order_manager.check_intrabar_triggers(
                current_price=current_price,
                session=session,
            )
            if sl_tp_closed:
                logger.info(f"Intrabar trigger closed trade: {sl_tp_closed['trade_id']} ({sl_tp_closed['exit_reason']})")

            # 3. Fetch latest candles from DB or Binance fallback
            df = await self.market_engine.get_candles_dataframe(
                symbol=self.symbol,
                timeframe=self.timeframe,
                limit=200,
                session=session,
            )

            if df.empty or len(df) < 50:
                return

            # 4. Check if we have a new closed candle or position change
            balances = order_manager.get_account_balances(current_price)
            current_equity = balances["total_equity"]
            active_pos = order_manager.get_active_position()

            # 5. Evaluate Multi-Factor Strategy Engine
            decision = strategy_engine.evaluate_decision(
                df_candles=df,
                account_equity=current_equity,
                current_open_position=active_pos,
            )
            decision["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.last_decision = decision

            # 6. Execute Trading Actions
            action = decision.get("action")

            if action == "BUY" and active_pos is None:
                # Check risk permission
                can_trade, denial_reason = risk_manager.drawdown_controller.can_open_new_trade(current_equity)
                if can_trade and decision.get("order_details"):
                    order_det = decision["order_details"]
                    logger.info(f"Executing BUY order based on strategy signal: {decision['reason']}")
                    await order_manager.open_position(
                        symbol=self.symbol,
                        price=current_price,
                        position_size_usd=order_det["position_size_usd"],
                        stop_loss=order_det["stop_loss"],
                        take_profit=order_det["take_profit"],
                        model_probability=decision.get("confidence"),
                        strategy_reason=decision.get("reason"),
                        explanation_json=json.dumps(decision.get("numerical_explanation", [])),
                        session=session,
                    )
                else:
                    logger.warning(f"Strategy signaled BUY but Risk Gatekeeper denied: {denial_reason}")

            elif action == "SELL" and active_pos is not None:
                logger.info(f"Executing SELL / CLOSE position based on strategy signal: {decision['reason']}")
                await order_manager.close_position(
                    exit_price=current_price,
                    exit_reason="STRATEGY_SELL",
                    session=session,
                )

            # 7. Periodically record equity snapshot (every ~12 ticks = 60s)
            if self.iteration_count % 12 == 0:
                equity_repo = EquityRepository(session)
                high_water = risk_manager.drawdown_controller.high_water_mark
                dd_pct = (high_water - current_equity) / high_water * 100.0 if high_water > 0 else 0.0

                snapshot = EquitySnapshot(
                    timestamp=datetime.now(timezone.utc),
                    total_equity=current_equity,
                    available_balance=balances["usdt_balance"],
                    unrealized_pnl=balances["unrealized_pnl"],
                    realized_pnl=balances["realized_pnl_total"],
                    drawdown_pct=dd_pct,
                    high_water_mark=high_water,
                    open_positions_count=1 if active_pos else 0,
                    mode=settings.TRADING_MODE,
                )
                await equity_repo.create(snapshot)


# Global singleton instance
bot_engine = TradingBotEngine()
