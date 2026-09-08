"""
Market data API endpoints for historical candles, ticker data, and background sync.
"""

from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.market_data import MarketDataEngine
from backend.app.database.database import get_db
from backend.app.database.models import Candle
from backend.app.execution.binance_client import BinanceClient

router = APIRouter(prefix="/market", tags=["Market Data"])
market_engine = MarketDataEngine()


@router.get("/ticker")
async def get_market_ticker(symbol: str = Query(default="BTCUSDT")):
    """Fetch live ticker and 24h price statistics from exchange."""
    client = BinanceClient()
    try:
        await client.initialize()
        ticker = await client.get_ticker(symbol=symbol.upper())
        return ticker.model_dump()
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "price": 91500.0,
            "bid_price": 91490.0,
            "ask_price": 91510.0,
            "volume_24h": 14500.0,
            "price_change_24h_pct": 1.25,
            "timestamp": 0,
            "status": "FALLBACK",
        }
    finally:
        await client.close()


@router.get("/watchlist")
async def get_market_watchlist():
    """Fetch live ticker and price statistics for all supported coins in parallel."""
    import asyncio
    from backend.app.core.config import SUPPORTED_SYMBOLS

    client = BinanceClient()
    try:
        await client.initialize()
        tasks = [client.get_ticker(symbol=sym) for sym in SUPPORTED_SYMBOLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        tickers = []
        for sym, res in zip(SUPPORTED_SYMBOLS, results):
            if isinstance(res, Exception):
                tickers.append({
                    "symbol": sym,
                    "price": 0.0,
                    "bid_price": 0.0,
                    "ask_price": 0.0,
                    "volume_24h": 0.0,
                    "price_change_24h_pct": 0.0,
                    "timestamp": 0,
                    "status": "FALLBACK",
                })
            else:
                tickers.append(res.model_dump())
        return tickers
    finally:
        await client.close()



@router.get("/candles")
async def get_candles(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical candlesticks from database."""
    stmt = (
        select(Candle)
        .where(Candle.symbol == symbol.upper(), Candle.timeframe == timeframe)
        .order_by(desc(Candle.timestamp))
        .limit(limit)
    )
    result = await db.execute(stmt)
    candles = list(result.scalars().all())

    # If no candles are stored yet for this coin/timeframe, auto-fetch from Binance
    if not candles:
        try:
            stored = await market_engine.fetch_and_store_historical_candles(
                symbol=symbol.upper(),
                timeframe=timeframe,
                limit=min(limit, 100),
                session=db,
            )
            if stored:
                candles = stored[-limit:]
        except Exception as e:
            logger.warning(f"Auto-fetch candles for {symbol} ({timeframe}) notice: {e}")

    # Return chronological order
    return [
        {
            "id": getattr(c, "id", i + 1),
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "timestamp": c.timestamp.isoformat() if hasattr(c.timestamp, "isoformat") else str(c.timestamp),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
            "quote_volume": getattr(c, "quote_volume", 0.0),
            "trades_count": getattr(c, "trades_count", 0),
            "is_closed": getattr(c, "is_closed", True),
        }
        for i, c in enumerate(reversed(candles))
    ]


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_candles(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=300, ge=10, le=1000),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """Synchronize latest historical candles from Binance into database."""
    try:
        stored = await market_engine.fetch_and_store_historical_candles(
            symbol=symbol.upper(),
            timeframe=timeframe,
            limit=limit,
            session=db,
        )
        return {
            "status": "SYNCED",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "count": len(stored),
            "message": f"Successfully ingested {len(stored)} candles for {symbol.upper()} ({timeframe})",
        }
    except Exception as e:
        logger.error(f"Failed to sync candles: {e}")
        return {
            "status": "ERROR",
            "message": f"Failed to sync candles: {str(e)}",
        }
