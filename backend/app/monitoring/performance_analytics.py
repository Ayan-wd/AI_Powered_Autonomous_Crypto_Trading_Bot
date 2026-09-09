"""
Institutional Quantitative Performance Analytics Engine.
Calculates risk-adjusted metrics, trade distribution, holding periods, payoff ratios,
Sharpe/Sortino ratios, and drawdown analytics from trade history and equity snapshots.
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from backend.app.database.models import EquitySnapshot, Trade


class PerformanceAnalyticsEngine:
    """Computes comprehensive quantitative performance analytics."""

    @staticmethod
    def calculate_trade_metrics(trades: List[Trade], starting_capital: float = 50.0) -> Dict[str, Any]:
        """Compute advanced trade performance statistics from closed trades."""
        closed_trades = [t for t in trades if t.status == "CLOSED" and t.exit_price is not None]

        if not closed_trades:
            return {
                "total_trades": 0,
                "closed_trades_count": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate_pct": 0.0,
                "profit_factor": 0.0,
                "expectancy_usd": 0.0,
                "expectancy_pct": 0.0,
                "total_realized_pnl": 0.0,
                "total_return_pct": 0.0,
                "total_fees_paid": 0.0,
                "average_win_usd": 0.0,
                "average_loss_usd": 0.0,
                "payoff_ratio": 0.0,
                "largest_win_usd": 0.0,
                "largest_loss_usd": 0.0,
                "average_holding_time_minutes": 0.0,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "exit_reasons_breakdown": {},
            }

        pnls = [t.pnl for t in closed_trades]
        pnl_pcts = [t.pnl_pct for t in closed_trades]
        fees = [t.fees for t in closed_trades]

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_realized_pnl = float(sum(pnls))
        total_fees = float(sum(fees))
        gross_profit = float(sum(wins))
        gross_loss = float(abs(sum(losses)))

        win_rate = (len(wins) / len(closed_trades)) * 100.0 if closed_trades else 0.0
        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 2)
        elif gross_profit > 0:
            profit_factor = round(gross_profit, 2)
        else:
            profit_factor = 0.0

        expectancy_usd = float(np.mean(pnls)) if pnls else 0.0
        expectancy_pct = float(np.mean(pnl_pcts) * 100.0) if pnl_pcts else 0.0

        avg_win = float(np.mean(wins)) if wins else 0.0
        avg_loss = float(abs(np.mean(losses))) if losses else 0.0
        payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # Holding times
        holding_minutes = []
        for t in closed_trades:
            if t.entry_time and t.exit_time:
                # Handle timezone compatibility
                diff = (t.exit_time - t.entry_time).total_seconds() / 60.0
                holding_minutes.append(max(0.0, diff))
        avg_hold_mins = float(np.mean(holding_minutes)) if holding_minutes else 0.0

        # Consecutive wins / losses streaks
        consecutive_wins = 0
        consecutive_losses = 0
        max_cons_wins = 0
        max_cons_losses = 0

        for p in pnls:
            if p > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_cons_wins = max(max_cons_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_cons_losses = max(max_cons_losses, consecutive_losses)

        # Exit reasons breakdown
        exit_reasons: Dict[str, int] = {}
        for t in closed_trades:
            reason = "SIGNAL_EXIT"
            if t.strategy_reason and "Closed:" in t.strategy_reason:
                reason = t.strategy_reason.split("Closed:")[-1].strip()
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

        return {
            "total_trades": len(trades),
            "closed_trades_count": len(closed_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "expectancy_usd": round(expectancy_usd, 3),
            "expectancy_pct": round(expectancy_pct, 2),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "total_return_pct": round((total_realized_pnl / starting_capital) * 100.0, 2),
            "total_fees_paid": round(total_fees, 4),
            "average_win_usd": round(avg_win, 2),
            "average_loss_usd": round(avg_loss, 2),
            "payoff_ratio": round(payoff_ratio, 2),
            "largest_win_usd": round(largest_win, 2),
            "largest_loss_usd": round(largest_loss, 2),
            "average_holding_time_minutes": round(avg_hold_mins, 1),
            "max_consecutive_wins": max_cons_wins,
            "max_consecutive_losses": max_cons_losses,
            "exit_reasons_breakdown": exit_reasons,
        }

    @staticmethod
    def calculate_equity_metrics(snapshots: List[EquitySnapshot], starting_capital: float = 50.0) -> Dict[str, Any]:
        """Compute portfolio risk-adjusted return metrics from equity time series."""
        if not snapshots or len(snapshots) < 2:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "max_drawdown_usd": 0.0,
                "peak_equity": starting_capital,
                "current_equity": snapshots[0].total_equity if snapshots else starting_capital,
            }

        # Ensure chronological order (oldest to newest)
        try:
            if snapshots[0].timestamp and snapshots[-1].timestamp and snapshots[0].timestamp > snapshots[-1].timestamp:
                chrono_snapshots = list(reversed(snapshots))
            else:
                chrono_snapshots = list(snapshots)
        except Exception:
            chrono_snapshots = list(snapshots)

        equities = [s.total_equity for s in chrono_snapshots]
        peak = starting_capital
        max_dd_pct = 0.0
        max_dd_usd = 0.0

        for eq in equities:
            if eq > peak:
                peak = eq
            dd_usd = peak - eq
            dd_pct = (dd_usd / peak) * 100.0 if peak > 0 else 0.0
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
            if dd_usd > max_dd_usd:
                max_dd_usd = dd_usd

        # Returns series
        eq_series = pd.Series(equities)
        pct_returns = eq_series.pct_change().dropna()

        if pct_returns.empty or len(pct_returns) < 2 or pd.isna(pct_returns.std()) or pct_returns.std() == 0:
            sharpe = 0.0
            sortino = 0.0
        else:
            mean_ret = pct_returns.mean()
            std_ret = pct_returns.std()
            # Annualization factor for ~15m snapshots (~35,040 periods/yr)
            annual_factor = np.sqrt(35040)
            sharpe = float((mean_ret / std_ret) * annual_factor) if (std_ret and not pd.isna(std_ret) and std_ret > 0) else 0.0

            downside_returns = pct_returns[pct_returns < 0]
            if len(downside_returns) >= 2 and not pd.isna(downside_returns.std()) and downside_returns.std() > 0:
                downside_std = downside_returns.std()
                sortino = float((mean_ret / downside_std) * annual_factor)
            elif std_ret and not pd.isna(std_ret) and std_ret > 0:
                sortino = float((mean_ret / std_ret) * annual_factor)
            else:
                sortino = 0.0

        if math.isnan(sharpe) or math.isinf(sharpe):
            sharpe = 0.0
        if math.isnan(sortino) or math.isinf(sortino):
            sortino = 0.0

        current_eq = equities[-1]
        total_return_pct = ((current_eq - starting_capital) / starting_capital) * 100.0
        calmar = (total_return_pct / max_dd_pct) if max_dd_pct > 0 else 0.0
        if math.isnan(calmar) or math.isinf(calmar):
            calmar = 0.0

        return {
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
            "max_drawdown_usd": round(max_dd_usd, 2),
            "peak_equity": round(peak, 2),
            "current_equity": round(current_eq, 2),
        }


# Global singleton
performance_engine = PerformanceAnalyticsEngine()
