"""
Strategy Decision API routes for evaluating live trade signals and position management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import get_db
from backend.app.database.repositories import EquityRepository
from backend.app.strategy.strategy_engine import strategy_engine

router = APIRouter(prefix="/strategy", tags=["Strategy Engine"])
market_engine = MarketDataEngine()


@router.get("/decision")
async def get_strategy_decision(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate the full multi-factor strategy + risk engine on latest candles
    and return the deterministic trade decision (BUY with sizing / SELL / HOLD).
    """
    try:
        df = await market_engine.get_candles_dataframe(
            symbol=symbol.upper(), timeframe=timeframe, limit=200, session=db
        )
        if df.empty or len(df) < 50:
            return {
                "action": "HOLD / NO TRADE",
                "reason": "Insufficient market candles to evaluate strategy.",
                "confidence": 0.0,
                "order_details": None,
                "numerical_explanation": ["Need at least 50 historical candles."],
            }

        equity_repo = EquityRepository(db)
        latest_snapshot = await equity_repo.get_latest()
        current_equity = latest_snapshot.total_equity if latest_snapshot else settings.STARTING_CAPITAL

        decision = strategy_engine.evaluate_decision(
            df_candles=df,
            account_equity=current_equity,
            current_open_position=None,
        )
        decision["symbol"] = symbol.upper()
        decision["timeframe"] = timeframe
        decision["account_equity"] = current_equity
        return decision
    except Exception as e:
        logger.error(f"Strategy decision evaluation error: {e}")
        return {
            "action": "HOLD / NO TRADE",
            "reason": f"Strategy evaluation error: {str(e)} -> Preserving capital.",
            "confidence": 1.0,
            "order_details": None,
            "numerical_explanation": [f"Exception: {str(e)}"],
        }
