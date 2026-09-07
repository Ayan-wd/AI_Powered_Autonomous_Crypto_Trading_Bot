"""
Backtesting API endpoints for historical simulation, metrics, and 3-way strategy benchmarking.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.backtesting.engine import BacktestEngine
from backend.app.backtesting.walk_forward import WalkForwardBacktester
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import get_db

router = APIRouter(prefix="/backtest", tags=["Backtesting"])
market_engine = MarketDataEngine()


@router.post("/run")
async def run_backtest(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    strategy: str = Query(default="AI_ML", description="AI_ML, TECHNICAL_CROSS, or BUY_AND_HOLD"),
    limit_candles: int = Query(default=500, ge=50, le=1000),
    starting_capital: float = Query(default=50.0, gt=0),
    fee_rate: float = Query(default=0.001),
    slippage_rate: float = Query(default=0.0005),
    stop_loss_pct: float = Query(default=0.015),
    take_profit_pct: float = Query(default=0.030),
    min_confidence: float = Query(default=0.65),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute backtest simulation on historical candles with realistic fees, slippage, and next-bar open fills.
    """
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=limit_candles, session=db
        )
        if len(df) < 50:
            return {"status": "ERROR", "message": f"Need at least 50 candles, got {len(df)}"}

        engine = BacktestEngine(
            starting_capital=starting_capital,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
        )

        result = engine.run(df, strategy_type=strategy, min_confidence=min_confidence)
        result["status"] = "SUCCESS"
        result["symbol"] = symbol.upper()
        result["timeframe"] = timeframe
        result["total_candles"] = len(df)
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return {"status": "ERROR", "message": str(e)}


@router.post("/benchmark")
async def run_benchmark_comparison(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit_candles: int = Query(default=500, ge=50, le=1000),
    starting_capital: float = Query(default=50.0, gt=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute 3-way comparative benchmark:
    1. Buy & Hold Benchmark
    2. Simple Technical Strategy (EMA 20/50 Golden Cross)
    3. AI Multi-Factor Quantitative Strategy (XGBoost + Regime Filters)
    """
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=limit_candles, session=db
        )
        if len(df) < 50:
            return {"status": "ERROR", "message": f"Need at least 50 candles, got {len(df)}"}

        engine = BacktestEngine(starting_capital=starting_capital)

        bnh_res = engine.run(df, strategy_type="BUY_AND_HOLD")
        tech_res = engine.run(df, strategy_type="TECHNICAL_CROSS")
        ai_res = engine.run(df, strategy_type="AI_ML")

        return {
            "status": "SUCCESS",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "candle_count": len(df),
            "starting_capital": starting_capital,
            "strategies": {
                "buy_and_hold": bnh_res["metrics"],
                "technical_cross": tech_res["metrics"],
                "ai_multi_factor": ai_res["metrics"],
            },
            "comparison": {
                "best_return_strategy": max(
                    [("Buy & Hold", bnh_res["metrics"]["total_return_pct"]),
                     ("EMA Cross", tech_res["metrics"]["total_return_pct"]),
                     ("AI Machine Learning", ai_res["metrics"]["total_return_pct"])],
                    key=lambda x: x[1]
                )[0],
                "lowest_drawdown_strategy": min(
                    [("Buy & Hold", bnh_res["metrics"]["max_drawdown_pct"]),
                     ("EMA Cross", tech_res["metrics"]["max_drawdown_pct"]),
                     ("AI Machine Learning", ai_res["metrics"]["max_drawdown_pct"])],
                    key=lambda x: x[1]
                )[0],
            }
        }
    except Exception as e:
        logger.error(f"Benchmark comparison failed: {e}")
        return {"status": "ERROR", "message": str(e)}


@router.post("/walk-forward")
async def run_walk_forward_backtest(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit_candles: int = Query(default=600, ge=120, le=1000),
    n_splits: int = Query(default=3, ge=2, le=5),
    db: AsyncSession = Depends(get_db),
):
    """Run sequential walk-forward backtest simulating rolling out-of-sample execution."""
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=limit_candles, session=db
        )
        wf_backtester = WalkForwardBacktester(n_splits=n_splits)
        result = wf_backtester.run(df)
        result["status"] = "SUCCESS"
        result["symbol"] = symbol.upper()
        result["timeframe"] = timeframe
        return result
    except Exception as e:
        logger.error(f"Walk-forward backtest failed: {e}")
        return {"status": "ERROR", "message": str(e)}
