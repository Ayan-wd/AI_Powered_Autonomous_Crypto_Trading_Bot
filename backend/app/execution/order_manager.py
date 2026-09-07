"""
Order and Position Execution Manager.
Orchestrates order routing between PaperExchangeSimulator and Live Exchange clients,
persisting full audit trails to SQLite/PostgreSQL and feeding realized PnL back into Risk Management.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.models import EquitySnapshot, Order, Trade
from backend.app.database.repositories import EquityRepository, LogRepository, OrderRepository, TradeRepository
from backend.app.execution.binance_client import BinanceClient
from backend.app.execution.paper_trading import PaperExchangeSimulator
from backend.app.risk.risk_manager import risk_manager


class OrderManager:
    """Master order execution coordinator for paper and live crypto trading."""

    def __init__(
        self,
        simulator: Optional[PaperExchangeSimulator] = None,
        binance_client: Optional[BinanceClient] = None,
    ):
        self.simulator = simulator or PaperExchangeSimulator(
            starting_capital=settings.STARTING_CAPITAL,
            fee_rate=0.001,  # 0.10%
            slippage_rate=0.0005,  # 0.05%
        )
        self.binance_client = binance_client or BinanceClient()

    def is_live_or_testnet(self) -> bool:
        """Check if trading mode is TESTNET or LIVE with safety flags enabled."""
        if settings.TRADING_MODE == "TESTNET" and settings.TRADING_ENABLED:
            return bool(settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET)
        if settings.TRADING_MODE == "LIVE" and settings.LIVE_TRADING and settings.TRADING_ENABLED:
            return bool(settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET)
        return False

    def get_active_position(self) -> Optional[Dict[str, Any]]:
        """Return active open position metadata if any."""
        if self.simulator.active_position:
            return self.simulator.active_position.to_dict()
        return None

    def get_account_balances(self, current_price: Optional[float] = None) -> Dict[str, Any]:
        """Return current wallet balances and total equity."""
        total_equity = self.simulator.get_total_equity(current_price)
        unrealized = self.simulator.active_position.unrealized_pnl if self.simulator.active_position else 0.0
        return {
            "usdt_balance": round(self.simulator.usdt_balance, 2),
            "total_equity": round(total_equity, 2),
            "unrealized_pnl": round(unrealized, 2),
            "realized_pnl_total": round(self.simulator.realized_pnl_total, 2),
            "total_fees_paid": round(self.simulator.total_fees_paid, 4),
            "has_open_position": self.simulator.active_position is not None,
            "mode": settings.TRADING_MODE,
        }

    async def open_position(
        self,
        symbol: str,
        price: float,
        position_size_usd: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        model_probability: Optional[float] = None,
        strategy_reason: Optional[str] = None,
        explanation_json: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Open a new long trading position according to risk parameters.
        Routes to Binance Testnet if authorized or Paper Simulator.
        Persists Order and Trade records to database.
        """
        is_paper = not self.is_live_or_testnet()
        exchange_order_id = None

        if not is_paper:
            # Route to Binance Spot Testnet
            try:
                raw_qty = position_size_usd / price
                logger.info(f"Routing live order to Binance Testnet: BUY {symbol} Qty={raw_qty:.6f}")
                testnet_res = await self.binance_client.place_order(
                    symbol=symbol,
                    side="BUY",
                    order_type="MARKET",
                    quantity=raw_qty,
                )
                exchange_order_id = str(testnet_res.get("orderId"))
                logger.info(f"Binance Testnet order placed: {exchange_order_id}")
            except Exception as e:
                logger.error(f"Binance Testnet order error: {e}. Falling back to paper execution for safety.")
                is_paper = True

        # Execute fill in simulator (tracks internal state)
        fill_res = self.simulator.execute_market_buy(
            symbol=symbol,
            price=price,
            position_size_usd=position_size_usd,
            stop_loss=stop_loss,
            take_profit=take_profit,
            model_probability=model_probability,
            strategy_reason=strategy_reason,
            explanation_json=explanation_json,
        )

        if fill_res.get("status") != "FILLED":
            return fill_res

        fill_res["is_paper"] = is_paper
        fill_res["exchange_order_id"] = exchange_order_id

        # Persist to database if session provided
        if session is not None:
            try:
                order_repo = OrderRepository(session)
                trade_repo = TradeRepository(session)
                log_repo = LogRepository(session)

                # 1. Create DB Order record
                db_order = Order(
                    client_order_id=fill_res["client_order_id"],
                    symbol=symbol,
                    side="BUY",
                    order_type="MARKET",
                    price=fill_res["entry_price"],
                    quantity=fill_res["quantity"],
                    filled_quantity=fill_res["quantity"],
                    status="FILLED",
                    is_paper=True,
                )
                await order_repo.create(db_order)

                # 2. Create DB Trade record
                db_trade = Trade(
                    trade_id=fill_res["trade_id"],
                    symbol=symbol,
                    side="BUY",
                    entry_price=fill_res["entry_price"],
                    quantity=fill_res["quantity"],
                    entry_time=datetime.now(timezone.utc),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    fees=fill_res["fee_usd"],
                    slippage=fill_res["slippage_usd"],
                    model_probability=model_probability,
                    strategy_reason=strategy_reason,
                    explanation_json=explanation_json,
                    status="OPEN",
                    is_paper=True,
                )
                await trade_repo.create(db_trade)

                # 3. Create Audit Log
                await log_repo.add_log(
                    level="INFO",
                    event_type="ORDER_FILLED",
                    message=f"BUY {symbol} filled at ${fill_res['entry_price']:.2f} (Size: ${position_size_usd:.2f})",
                    details_json=json.dumps(fill_res),
                )
            except Exception as e:
                logger.error(f"Error persisting open trade to database: {e}")

        return fill_res

    async def close_position(
        self,
        exit_price: float,
        exit_reason: str = "SIGNAL_EXIT",
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Close active trading position, compute realized PnL, update DrawdownController,
        and persist closed trade and equity snapshot to database.
        """
        closed_summary = self.simulator.execute_market_sell(exit_price=exit_price, exit_reason=exit_reason)
        if not closed_summary:
            return None

        # Update Master Risk Drawdown Controller
        current_equity = self.simulator.get_total_equity(exit_price)
        risk_manager.drawdown_controller.update_equity_state(
            current_equity=current_equity,
            trade_pnl=closed_summary["pnl"],
        )

        # Persist to database if session provided
        if session is not None:
            try:
                trade_repo = TradeRepository(session)
                equity_repo = EquityRepository(session)
                log_repo = LogRepository(session)

                # 1. Update Trade Record
                db_trade = await trade_repo.get_by_id(closed_summary["trade_id"])
                if db_trade:
                    db_trade.exit_price = closed_summary["exit_price"]
                    db_trade.exit_time = closed_summary["exit_time"]
                    db_trade.pnl = closed_summary["pnl"]
                    db_trade.pnl_pct = closed_summary["pnl_pct"]
                    db_trade.fees += closed_summary["fees"]
                    db_trade.status = "CLOSED"
                    db_trade.strategy_reason = closed_summary["strategy_reason"]
                    await trade_repo.update(db_trade)

                # 2. Record Equity Snapshot
                snapshot = EquitySnapshot(
                    timestamp=datetime.now(timezone.utc),
                    total_equity=current_equity,
                    available_balance=self.simulator.usdt_balance,
                    unrealized_pnl=0.0,
                    realized_pnl=closed_summary["pnl"],
                    drawdown_pct=(risk_manager.drawdown_controller.high_water_mark - current_equity)
                    / risk_manager.drawdown_controller.high_water_mark
                    * 100.0,
                    high_water_mark=risk_manager.drawdown_controller.high_water_mark,
                    open_positions_count=0,
                    mode="PAPER",
                )
                await equity_repo.create(snapshot)

                # 3. Create Audit Log
                await log_repo.add_log(
                    level="INFO",
                    event_type="POSITION_CLOSED",
                    message=(
                        f"CLOSED {closed_summary['symbol']} at ${closed_summary['exit_price']:.2f} | "
                        f"PnL: ${closed_summary['pnl']:.2f} ({closed_summary['pnl_pct'] * 100:.2f}%) | "
                        f"Reason: {exit_reason}"
                    ),
                    details_json=json.dumps(closed_summary, default=str),
                )
            except Exception as e:
                logger.error(f"Error persisting closed trade to database: {e}")

        return closed_summary

    async def check_intrabar_triggers(
        self,
        current_price: float,
        candle_high: Optional[float] = None,
        candle_low: Optional[float] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate SL/TP hits on active position."""
        if not self.simulator.active_position:
            return None

        pos = self.simulator.active_position
        high_val = candle_high if candle_high is not None else current_price
        low_val = candle_low if candle_low is not None else current_price

        # Check Stop Loss
        if pos.stop_loss is not None and low_val <= pos.stop_loss:
            return await self.close_position(
                exit_price=pos.stop_loss, exit_reason="STOP_LOSS", session=session
            )

        # Check Take Profit
        if pos.take_profit is not None and high_val >= pos.take_profit:
            return await self.close_position(
                exit_price=pos.take_profit, exit_reason="TAKE_PROFIT", session=session
            )

        # Just update mark price
        pos.update_mark_price(current_price)
        return None

    def reset_paper_account(self, starting_capital: Optional[float] = None) -> None:
        """Reset simulator wallet and risk manager states."""
        cap = starting_capital or settings.STARTING_CAPITAL
        self.simulator.reset_account(cap)
        risk_manager.drawdown_controller.starting_capital = cap
        risk_manager.drawdown_controller.high_water_mark = cap
        risk_manager.drawdown_controller.daily_starting_equity = cap
        risk_manager.drawdown_controller.daily_realized_loss = 0.0
        risk_manager.drawdown_controller.weekly_realized_loss = 0.0
        risk_manager.drawdown_controller.consecutive_losses = 0
        risk_manager.drawdown_controller.daily_trades_count = 0
        risk_manager.drawdown_controller.is_circuit_breaker_active = False
        risk_manager.drawdown_controller.circuit_breaker_reason = None
        logger.info("OrderManager and RiskManager reset to clean baseline.")


# Singleton global order manager instance
order_manager = OrderManager()
