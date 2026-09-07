"""
Realistic Crypto Backtesting Engine.
Simulates order fills, maker/taker fees, market slippage, intra-bar stop-loss/take-profit,
and next-bar open execution timing ($t+1$) with zero lookahead bias.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.backtesting.metrics import PerformanceMetricsCalculator
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.features.feature_engineering import FEATURE_COLUMNS, FeaturePipeline
from backend.app.ml.predict import PredictionEngine


class BacktestEngine:
    """Institutional-grade backtesting simulator."""

    def __init__(
        self,
        starting_capital: float = 50.0,
        fee_rate: float = 0.001,  # 0.10% Binance Spot maker/taker fee
        slippage_rate: float = 0.0005,  # 0.05% slippage on market orders
        max_position_size_usd: float = 10.0,  # Max $10 on $50 account
        stop_loss_pct: float = 0.015,  # 1.5% stop loss
        take_profit_pct: float = 0.030,  # 3.0% take profit (2:1 R:R)
    ):
        self.starting_capital = starting_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.max_position_size = min(max_position_size_usd, starting_capital)
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def run(
        self,
        df_candles: pd.DataFrame,
        strategy_type: str = "AI_ML",  # "AI_ML", "TECHNICAL_CROSS", "BUY_AND_HOLD"
        min_confidence: float = 0.65,
    ) -> Dict[str, Any]:
        """
        Execute backtest over historical candlestick DataFrame.
        """
        if df_candles.empty or len(df_candles) < 20:
            raise ValueError(f"Need at least 20 candles to run backtest, got {len(df_candles)}")

        df = df_candles.copy()
        df.sort_index(inplace=True)

        if strategy_type == "BUY_AND_HOLD":
            return self._run_buy_and_hold(df)

        # Compute technical features
        df_features = FeaturePipeline.build_features(df, drop_na=False)

        # Simulation state
        capital = self.starting_capital
        position_qty = 0.0
        position_entry_price = 0.0
        position_stop_loss = 0.0
        position_take_profit = 0.0
        position_entry_idx = 0

        trades: List[Dict[str, Any]] = []
        equity_series: List[float] = []
        timestamps: List[Any] = []

        pending_signal = None  # Signal generated at close of t, executed at open of t+1

        n_bars = len(df_features)
        for i in range(n_bars):
            row = df_features.iloc[i]
            ts = df_features.index[i]
            open_p = float(row["open"])
            high_p = float(row["high"])
            low_p = float(row["low"])
            close_p = float(row["close"])

            # 1. Execute any pending signal from previous bar's close at this bar's OPEN price
            if pending_signal == "BUY" and position_qty == 0.0 and capital > 5.0:
                alloc = min(self.max_position_size, capital)
                exec_price = open_p * (1.0 + self.slippage_rate)
                fee = alloc * self.fee_rate
                slippage_cost = alloc * self.slippage_rate

                position_qty = (alloc - fee) / exec_price
                capital -= alloc
                position_entry_price = exec_price
                position_stop_loss = exec_price * (1.0 - self.stop_loss_pct)
                position_take_profit = exec_price * (1.0 + self.take_profit_pct)
                position_entry_idx = i

            elif pending_signal == "SELL" and position_qty > 0.0:
                exec_price = open_p * (1.0 - self.slippage_rate)
                gross_val = position_qty * exec_price
                fee = gross_val * self.fee_rate
                slippage_cost = gross_val * self.slippage_rate
                net_val = gross_val - fee

                pnl = net_val - (position_qty * position_entry_price)
                pnl_pct = (pnl / (position_qty * position_entry_price)) * 100.0
                capital += net_val

                trades.append({
                    "entry_time": str(df_features.index[position_entry_idx]),
                    "exit_time": str(ts),
                    "entry_price": round(position_entry_price, 2),
                    "exit_price": round(exec_price, 2),
                    "quantity": round(position_qty, 6),
                    "pnl": round(pnl, 4),
                    "pnl_pct": round(pnl_pct, 2),
                    "fees": round(fee, 4),
                    "slippage": round(slippage_cost, 4),
                    "exit_reason": "SIGNAL_EXIT",
                    "bars_held": i - position_entry_idx,
                })
                position_qty = 0.0

            pending_signal = None

            # 2. Check Intra-bar Stop Loss and Take Profit on active position
            if position_qty > 0.0:
                # Stop loss hit
                if low_p <= position_stop_loss:
                    exec_price = position_stop_loss * (1.0 - self.slippage_rate)
                    gross_val = position_qty * exec_price
                    fee = gross_val * self.fee_rate
                    net_val = gross_val - fee
                    pnl = net_val - (position_qty * position_entry_price)
                    pnl_pct = (pnl / (position_qty * position_entry_price)) * 100.0
                    capital += net_val

                    trades.append({
                        "entry_time": str(df_features.index[position_entry_idx]),
                        "exit_time": str(ts),
                        "entry_price": round(position_entry_price, 2),
                        "exit_price": round(exec_price, 2),
                        "quantity": round(position_qty, 6),
                        "pnl": round(pnl, 4),
                        "pnl_pct": round(pnl_pct, 2),
                        "fees": round(fee, 4),
                        "slippage": round(position_qty * position_stop_loss * self.slippage_rate, 4),
                        "exit_reason": "STOP_LOSS",
                        "bars_held": i - position_entry_idx,
                    })
                    position_qty = 0.0

                # Take profit hit
                elif high_p >= position_take_profit:
                    exec_price = position_take_profit * (1.0 - self.slippage_rate)
                    gross_val = position_qty * exec_price
                    fee = gross_val * self.fee_rate
                    net_val = gross_val - fee
                    pnl = net_val - (position_qty * position_entry_price)
                    pnl_pct = (pnl / (position_qty * position_entry_price)) * 100.0
                    capital += net_val

                    trades.append({
                        "entry_time": str(df_features.index[position_entry_idx]),
                        "exit_time": str(ts),
                        "entry_price": round(position_entry_price, 2),
                        "exit_price": round(exec_price, 2),
                        "quantity": round(position_qty, 6),
                        "pnl": round(pnl, 4),
                        "pnl_pct": round(pnl_pct, 2),
                        "fees": round(fee, 4),
                        "slippage": round(position_qty * position_take_profit * self.slippage_rate, 4),
                        "exit_reason": "TAKE_PROFIT",
                        "bars_held": i - position_entry_idx,
                    })
                    position_qty = 0.0

            # 3. Track continuous equity at close of bar
            current_equity = capital + (position_qty * close_p)
            equity_series.append(current_equity)
            timestamps.append(ts)

            # 4. Generate Signal at Bar Close
            if i >= 15 and (i + 1) < n_bars:
                if strategy_type == "AI_ML":
                    pending_signal = self._evaluate_ai_strategy(row, min_confidence)
                elif strategy_type == "TECHNICAL_CROSS":
                    pending_signal = self._evaluate_technical_cross_strategy(row, df_features.iloc[i - 1])

        # Close any lingering open position at end of backtest
        if position_qty > 0.0:
            last_close = float(df_features.iloc[-1]["close"])
            gross_val = position_qty * last_close
            fee = gross_val * self.fee_rate
            net_val = gross_val - fee
            pnl = net_val - (position_qty * position_entry_price)
            capital += net_val
            trades.append({
                "entry_time": str(df_features.index[position_entry_idx]),
                "exit_time": str(df_features.index[-1]),
                "entry_price": round(position_entry_price, 2),
                "exit_price": round(last_close, 2),
                "quantity": round(position_qty, 6),
                "pnl": round(pnl, 4),
                "pnl_pct": round((pnl / (position_qty * position_entry_price)) * 100.0, 2),
                "fees": round(fee, 4),
                "slippage": 0.0,
                "exit_reason": "BACKTEST_END",
                "bars_held": n_bars - 1 - position_entry_idx,
            })
            equity_series[-1] = capital

        equity_curve = pd.Series(equity_series, index=timestamps)
        metrics = PerformanceMetricsCalculator.calculate(
            trades=trades,
            equity_curve=equity_curve,
            starting_capital=self.starting_capital,
        )

        return {
            "strategy": strategy_type,
            "metrics": metrics,
            "trades": trades,
            "equity_curve": [
                {"timestamp": str(ts), "equity": round(eq, 2)}
                for ts, eq in zip(timestamps[:: max(1, len(timestamps) // 100)], equity_series[:: max(1, len(equity_series) // 100)])
            ],
        }

    def _evaluate_ai_strategy(self, row: pd.Series, min_confidence: float) -> Optional[str]:
        """Evaluate AI machine learning probability strategy."""
        prediction = PredictionEngine.predict_from_features(row)
        decision = prediction["decision"]
        confidence = prediction["confidence"]

        if decision == "BUY" and confidence >= min_confidence:
            return "BUY"
        elif decision == "SELL" and confidence >= min_confidence:
            return "SELL"
        return None

    def _evaluate_technical_cross_strategy(self, current: pd.Series, prev: pd.Series) -> Optional[str]:
        """Simple baseline EMA 20 / EMA 50 golden cross strategy."""
        ema20_curr = float(current.get("ema_20", 0.0))
        ema50_curr = float(current.get("ema_50", 0.0))
        ema20_prev = float(prev.get("ema_20", 0.0))
        ema50_prev = float(prev.get("ema_50", 0.0))
        rsi = float(current.get("rsi_14", 50.0))

        if ema20_prev <= ema50_prev and ema20_curr > ema50_curr and 45 <= rsi <= 65:
            return "BUY"
        elif ema20_prev >= ema50_prev and ema20_curr < ema50_curr:
            return "SELL"
        return None

    def _run_buy_and_hold(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simulate Buy & Hold benchmark."""
        first_open = float(df.iloc[0]["open"]) * (1.0 + self.slippage_rate)
        fee = self.starting_capital * self.fee_rate
        qty = (self.starting_capital - fee) / first_open

        close_prices = df["close"].astype(float).values
        equity_series = (qty * close_prices).tolist()
        equity_curve = pd.Series(equity_series, index=df.index)

        last_close = float(df.iloc[-1]["close"]) * (1.0 - self.slippage_rate)
        exit_fee = (qty * last_close) * self.fee_rate
        final_pnl = (qty * last_close - exit_fee) - self.starting_capital

        trades = [
            {
                "entry_time": str(df.index[0]),
                "exit_time": str(df.index[-1]),
                "entry_price": round(first_open, 2),
                "exit_price": round(last_close, 2),
                "quantity": round(qty, 6),
                "pnl": round(final_pnl, 4),
                "pnl_pct": round((final_pnl / self.starting_capital) * 100.0, 2),
                "fees": round(fee + exit_fee, 4),
                "slippage": 0.0,
                "exit_reason": "BUY_AND_HOLD_END",
                "bars_held": len(df),
            }
        ]

        metrics = PerformanceMetricsCalculator.calculate(
            trades=trades,
            equity_curve=equity_curve,
            starting_capital=self.starting_capital,
        )

        return {
            "strategy": "BUY_AND_HOLD",
            "metrics": metrics,
            "trades": trades,
            "equity_curve": [
                {"timestamp": str(ts), "equity": round(eq, 2)}
                for ts, eq in zip(df.index[:: max(1, len(df) // 100)], equity_series[:: max(1, len(equity_series) // 100)])
            ],
        }
