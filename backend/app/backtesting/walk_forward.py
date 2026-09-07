"""
Walk-Forward Performance Backtesting.
Simulates realistic out-of-sample trading performance by rolling forward
through train -> test -> trade windows sequentially.
"""

from typing import Any, Dict, List
import pandas as pd
from backend.app.backtesting.engine import BacktestEngine
from backend.app.core.logging import logger
from backend.app.ml.train import ModelTrainer


class WalkForwardBacktester:
    """Walk-Forward Backtest Simulator."""

    def __init__(
        self,
        starting_capital: float = 50.0,
        n_splits: int = 3,
        horizon_candles: int = 4,
        return_threshold: float = 0.005,
    ):
        self.starting_capital = starting_capital
        self.n_splits = n_splits
        self.horizon = horizon_candles
        self.return_threshold = return_threshold

    def run(self, df_candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute sequential walk-forward backtest.
        """
        if len(df_candles) < 120:
            raise ValueError(f"Need at least 120 candles for walk-forward backtesting, got {len(df_candles)}")

        n_samples = len(df_candles)
        min_train = 60
        test_step = max(20, (n_samples - min_train) // self.n_splits)

        all_oos_trades: List[Dict[str, Any]] = []
        fold_reports: List[Dict[str, Any]] = []
        current_capital = self.starting_capital

        engine = BacktestEngine(starting_capital=current_capital)

        for fold in range(self.n_splits):
            train_end = min_train + (fold * test_step)
            test_end = min(train_end + test_step, n_samples)

            if train_end >= n_samples or (test_end - train_end) < 10:
                break

            df_train = df_candles.iloc[:train_end]
            # Pass full historical window up to test_end so technical indicators have full warmup history
            df_full_test_window = df_candles.iloc[:test_end]
            df_test_only = df_candles.iloc[train_end:test_end]

            # 1. Train model on historical slice
            trainer = ModelTrainer(horizon_candles=self.horizon, return_threshold=self.return_threshold)
            X_train, y_train = trainer.prepare_dataset(df_train)
            trainer.train_final_model(X_train, y_train, save=True)

            # 2. Run backtest on test slice with full historical warmup
            engine.starting_capital = current_capital
            backtest_res = engine.run(df_full_test_window, strategy_type="AI_ML")

            # Filter trades to only those that occurred strictly within the out-of-sample test window
            test_start_str = str(df_test_only.index[0])
            fold_trades = [
                t for t in backtest_res["trades"]
                if t["entry_time"] >= test_start_str
            ]
            all_oos_trades.extend(fold_trades)
            current_capital = backtest_res["metrics"]["final_equity"]

            fold_reports.append({
                "fold": fold + 1,
                "train_period": f"{df_train.index[0]} to {df_train.index[-1]} ({len(df_train)} bars)",
                "test_period": f"{df_test_only.index[0]} to {df_test_only.index[-1]} ({len(df_test_only)} bars)",
                "metrics": backtest_res["metrics"],
            })

        return {
            "total_folds": len(fold_reports),
            "starting_capital": self.starting_capital,
            "final_equity": round(current_capital, 2),
            "net_profit": round(current_capital - self.starting_capital, 2),
            "total_return_pct": round(((current_capital - self.starting_capital) / self.starting_capital) * 100.0, 2),
            "total_oos_trades": len(all_oos_trades),
            "fold_reports": fold_reports,
        }
