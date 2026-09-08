"""
Continuous Autonomous Trading Bot Engine.
Asynchronous execution loop that processes live market ticks, evaluates multi-factor strategy signals,
enforces institutional risk rules, and automatically executes paper or live orders.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json
import httpx

from backend.app.api.websocket.ws_manager import ws_manager
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
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"Market connection transient timeout during tick: {e}. Retrying next tick...")
            except Exception as e:
                logger.error(f"Error in trading bot tick loop: {e}", exc_info=True)

            await asyncio.sleep(self.tick_interval_sec)

    async def _tick(self) -> None:
        """Execute one evaluation tick with multi-coin scanner support."""
        async with async_session_factory() as session:
            active_pos = order_manager.get_active_position()

            # 1. If we have an open position, prioritize managing that specific coin
            if active_pos:
                pos_symbol = active_pos["symbol"]
                ticker = await self.market_engine.get_live_ticker(pos_symbol)
                current_price = ticker.price

                await ws_manager.broadcast("TICKER_UPDATE", {
                    "symbol": ticker.symbol,
                    "price": ticker.price,
                    "bid_price": ticker.bid_price,
                    "ask_price": ticker.ask_price,
                    "price_change_24h_pct": ticker.price_change_24h_pct,
                    "volume_24h": ticker.volume_24h,
                    "timestamp": ticker.timestamp,
                })

                sl_tp_closed = await order_manager.check_intrabar_triggers(
                    current_price=current_price,
                    session=session,
                    bid_price=ticker.bid_price,
                    ask_price=ticker.ask_price,
                )
                if sl_tp_closed:
                    logger.info(f"Intrabar trigger closed trade: {sl_tp_closed['trade_id']} ({sl_tp_closed['exit_reason']})")
                    await ws_manager.broadcast("POSITION_CLOSED", sl_tp_closed)
                    await ws_manager.broadcast("POSITION_UPDATE", None)
                    return

                # Update trailing decision on open position
                df = await self.market_engine.get_candles_dataframe(
                    symbol=pos_symbol,
                    timeframe=self.timeframe,
                    limit=100,
                    session=session,
                )
                if not df.empty:
                    balances = order_manager.get_account_balances(current_price)
                    decision = strategy_engine.evaluate_decision(
                        df_candles=df,
                        account_equity=balances["total_equity"],
                        current_open_position=active_pos,
                        symbol=pos_symbol,
                        current_market_price=current_price,
                    )
                    decision["timestamp"] = datetime.now(timezone.utc).isoformat()
                    self.last_decision = decision
                    await ws_manager.broadcast("STRATEGY_DECISION", decision)

                    # Check manual/strategy exit
                    if decision.get("action") == "SELL":
                        close_res = await order_manager.close_position(
                            exit_price=current_price,
                            exit_reason="STRATEGY_SELL",
                            session=session,
                            bid_price=ticker.bid_price,
                        )
                        if close_res:
                            await ws_manager.broadcast("POSITION_CLOSED", close_res)
                            await ws_manager.broadcast("POSITION_UPDATE", None)
                return

            # 2. No active position open -> Scan candidate coin(s)
            symbols_to_scan = (
                settings.SUPPORTED_SYMBOLS
                if self.symbol in ("ALL", "MULTI", "WATCHLIST")
                else [self.symbol]
            )

            balances = order_manager.get_account_balances()
            current_equity = balances["total_equity"]
            can_trade, denial_reason = risk_manager.drawdown_controller.can_open_new_trade(current_equity)
            if not can_trade:
                logger.warning(f"Risk Gatekeeper preventing new trades: {denial_reason}")
                return

            for sym in symbols_to_scan:
                try:
                    ticker = await self.market_engine.get_live_ticker(sym)
                    current_price = ticker.price

                    await ws_manager.broadcast("TICKER_UPDATE", {
                        "symbol": ticker.symbol,
                        "price": ticker.price,
                        "bid_price": ticker.bid_price,
                        "ask_price": ticker.ask_price,
                        "price_change_24h_pct": ticker.price_change_24h_pct,
                        "volume_24h": ticker.volume_24h,
                        "timestamp": ticker.timestamp,
                    })

                    df = await self.market_engine.get_candles_dataframe(
                        symbol=sym,
                        timeframe=self.timeframe,
                        limit=100,
                        session=session,
                    )
                    if df.empty or len(df) < 50:
                        continue

                    decision = strategy_engine.evaluate_decision(
                        df_candles=df,
                        account_equity=current_equity,
                        current_open_position=None,
                        symbol=sym,
                        current_market_price=current_price,
                    )
                    decision["timestamp"] = datetime.now(timezone.utc).isoformat()
                    self.last_decision = decision
                    await ws_manager.broadcast("STRATEGY_DECISION", decision)

                    action = decision.get("action")
                    if action == "BUY" and decision.get("order_details"):
                        order_det = decision["order_details"]
                        logger.info(f"Executing BUY order on {sym}: {decision['reason']}")
                        open_res = await order_manager.open_position(
                            symbol=sym,
                            price=current_price,
                            position_size_usd=order_det.get("position_size_usd") or order_det.get("position_value_usd", 10.0),
                            stop_loss=order_det["stop_loss"],
                            take_profit=order_det["take_profit"],
                            model_probability=decision.get("confidence"),
                            strategy_reason=decision.get("reason"),
                            explanation_json=json.dumps(decision.get("numerical_explanation", [])),
                            session=session,
                            ask_price=ticker.ask_price,
                            bid_price=ticker.bid_price,
                        )
                        if open_res.get("status") != "FILLED":
                            logger.warning(f"Order rejected by OrderManager: {open_res.get('reason')}")
                            continue

                        await ws_manager.broadcast("ORDER_FILLED", open_res)
                        await ws_manager.broadcast("POSITION_UPDATE", order_manager.get_active_position())
                        # Only 1 position at a time (anti-Martingale & capital preservation)
                        break
                except Exception as e:
                    logger.warning(f"Error scanning candidate coin {sym}: {e}")

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
                await ws_manager.broadcast("EQUITY_UPDATE", {
                    "total_equity": round(current_equity, 2),
                    "drawdown_pct": round(dd_pct, 2),
                    "unrealized_pnl": round(balances["unrealized_pnl"], 2),
                })


# Global singleton instance
bot_engine = TradingBotEngine()
