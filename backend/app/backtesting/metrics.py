"""
Financial & Quantitative Backtesting Performance Metrics.
Calculates institutional-grade risk-adjusted return metrics including Sharpe, Sortino,
Profit Factor, Maximum Drawdown, Expectancy, and Fee Impact.
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


class PerformanceMetricsCalculator:
    """Calculates comprehensive trading performance statistics from backtest results."""

    @staticmethod
    def calculate(
        trades: List[Dict[str, Any]],
        equity_curve: pd.Series,
        starting_capital: float = 50.0,
        risk_free_rate: float = 0.02,  # 2% annual risk-free rate
        timeframe_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Calculate complete metric battery.
        """
        if equity_curve.empty or len(equity_curve) < 2:
            return PerformanceMetricsCalculator._empty_metrics(starting_capital)

        final_equity = float(equity_curve.iloc[-1])
        net_profit = final_equity - starting_capital
        total_return_pct = (net_profit / starting_capital) * 100.0 if starting_capital > 0 else 0.0

        # Drawdown calculation
        rolling_max = equity_curve.cummax()
        drawdown_series = (equity_curve - rolling_max) / rolling_max
        max_drawdown_pct = float(abs(drawdown_series.min()))

        # Periodic returns for Sharpe / Sortino
        periodic_returns = equity_curve.pct_change().dropna()
        # Annualization factor for 15-minute crypto candles (365 days * 24 hrs * 4 bars/hr = 35,040 bars/yr)
        bars_per_year = (365 * 24 * 60) / max(timeframe_minutes, 1)

        # Sharpe Ratio
        mean_ret = periodic_returns.mean()
        std_ret = periodic_returns.std()
        rf_per_bar = (1 + risk_free_rate) ** (1 / bars_per_year) - 1

        if std_ret > 0 and len(periodic_returns) > 1:
            sharpe_ratio = float((mean_ret - rf_per_bar) / std_ret * np.sqrt(bars_per_year))
        else:
            sharpe_ratio = 0.0

        # Sortino Ratio (downside deviation only)
        downside_returns = periodic_returns[periodic_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 1 else 0.0
        if downside_std > 0:
            sortino_ratio = float((mean_ret - rf_per_bar) / downside_std * np.sqrt(bars_per_year))
        else:
            sortino_ratio = sharpe_ratio if sharpe_ratio > 0 else 0.0

        # Trade-specific statistics
        total_trades = len(trades)
        if total_trades == 0:
            return {
                "starting_capital": starting_capital,
                "final_equity": round(final_equity, 2),
                "net_profit": round(net_profit, 2),
                "total_return_pct": round(total_return_pct, 2),
                "max_drawdown_pct": round(max_drawdown_pct * 100, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "sortino_ratio": round(sortino_ratio, 2),
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "average_trade_pnl": 0.0,
                "expectancy": 0.0,
                "total_fees_paid": 0.0,
                "total_slippage_paid": 0.0,
                "max_consecutive_losses": 0,
                "exposure_pct": 0.0,
            }

        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] <= 0]

        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        total_fees = sum(t.get("fees", 0.0) for t in trades)
        total_slippage = sum(t.get("slippage", 0.0) for t in trades)

        win_rate = (len(winning_trades) / total_trades) * 100.0
        avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0.0
        avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0.0
        avg_trade = net_profit / total_trades

        # Profit Factor
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = 999.0 if gross_profit > 0 else 0.0

        # Mathematical Expectancy: (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        win_rate_dec = len(winning_trades) / total_trades
        loss_rate_dec = 1.0 - win_rate_dec
        expectancy = (win_rate_dec * avg_win) - (loss_rate_dec * avg_loss)

        # Consecutive losses
        max_cons_losses = 0
        current_cons_losses = 0
        for t in trades:
            if t["pnl"] <= 0:
                current_cons_losses += 1
                if current_cons_losses > max_cons_losses:
                    max_cons_losses = current_cons_losses
            else:
                current_cons_losses = 0

        # Market exposure time (fraction of bars with open position)
        bars_in_market = sum(t.get("bars_held", 1) for t in trades)
        exposure_pct = min(100.0, (bars_in_market / max(len(equity_curve), 1)) * 100.0)

        return {
            "starting_capital": starting_capital,
            "final_equity": round(final_equity, 2),
            "net_profit": round(net_profit, 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "average_win": round(avg_win, 4),
            "average_loss": round(avg_loss, 4),
            "average_trade_pnl": round(avg_trade, 4),
            "expectancy": round(expectancy, 4),
            "total_fees_paid": round(total_fees, 4),
            "total_slippage_paid": round(total_slippage, 4),
            "max_consecutive_losses": max_cons_losses,
            "exposure_pct": round(exposure_pct, 2),
        }

    @staticmethod
    def _empty_metrics(starting_capital: float) -> Dict[str, Any]:
        return {
            "starting_capital": starting_capital,
            "final_equity": starting_capital,
            "net_profit": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "average_trade_pnl": 0.0,
            "expectancy": 0.0,
            "total_fees_paid": 0.0,
            "total_slippage_paid": 0.0,
            "max_consecutive_losses": 0,
            "exposure_pct": 0.0,
        }
