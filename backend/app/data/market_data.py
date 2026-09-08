"""
Market Data Engine.
Manages downloading, caching, continuous persistence, and DataFrame formatting of OHLCV candlesticks.
"""

from datetime import datetime, timezone
from typing import List, Optional
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.data_validator import MarketDataValidator
from backend.app.database.models import Candle
from backend.app.execution.binance_client import BinanceClient
from backend.app.execution.exchange_interface import ExchangeInterface, TickerData


class MarketDataEngine:
    """Engine responsible for fetching, validating, and persisting market candles."""

    def __init__(self, exchange_client: Optional[ExchangeInterface] = None):
        self.client = exchange_client or BinanceClient()

    async def get_live_ticker(self, symbol: str) -> TickerData:
        """Fetch real-time ticker data from exchange adapter."""
        await self.client.initialize()
        return await self.client.get_ticker(symbol)

    async def fetch_and_store_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        session: Optional[AsyncSession] = None,
    ) -> List[Candle]:
        """Fetch historical candles from exchange, validate, and persist to DB."""
        await self.client.initialize()
        raw_klines = await self.client.get_klines(symbol=symbol, interval=timeframe, limit=limit)

        valid_klines, issues = MarketDataValidator.validate_sequence(raw_klines, timeframe=timeframe)
        if issues:
            logger.warning(f"Data validation notices for {symbol} ({timeframe}): {len(issues)} issues logged.")

        candle_models: List[Candle] = []
        for k in valid_klines:
            dt = datetime.fromtimestamp(k["timestamp"] / 1000.0, tz=timezone.utc)
            candle_models.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=dt,
                    open=k["open"],
                    high=k["high"],
                    low=k["low"],
                    close=k["close"],
                    volume=k["volume"],
                    quote_volume=k.get("quote_volume"),
                    trades_count=k.get("trades_count"),
                    is_closed=k.get("is_closed", True),
                )
            )

        if session and candle_models:
            # Upsert / insert new candles (avoid duplicate key violations)
            for c in candle_models:
                # Check if exists
                stmt = select(Candle).where(
                    Candle.symbol == c.symbol,
                    Candle.timeframe == c.timeframe,
                    Candle.timestamp == c.timestamp,
                )
                existing = (await session.execute(stmt)).scalars().first()
                if not existing:
                    session.add(c)
                else:
                    existing.open = c.open
                    existing.high = c.high
                    existing.low = c.low
                    existing.close = c.close
                    existing.volume = c.volume
                    existing.quote_volume = c.quote_volume
                    existing.trades_count = c.trades_count
            await session.commit()
            logger.info(f"Stored {len(candle_models)} validated candles for {symbol} ({timeframe})")

        return candle_models

    async def get_candles_dataframe(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        session: Optional[AsyncSession] = None,
    ) -> pd.DataFrame:
        """
        Retrieve candles as a clean Pandas DataFrame with UTC DatetimeIndex.
        If database has insufficient candles, automatically fetches from exchange.
        """
        candles: List[Candle] = []
        if session:
            stmt = (
                select(Candle)
                .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
                .order_by(desc(Candle.timestamp))
                .limit(limit)
            )
            res = await session.execute(stmt)
            candles = list(res.scalars().all())

        if len(candles) < limit:
            logger.info(f"Local DB has only {len(candles)} candles. Fetching fresh {limit} candles from exchange...")
            candles = await self.fetch_and_store_historical_candles(
                symbol=symbol, timeframe=timeframe, limit=limit, session=session
            )

        candles = sorted(candles, key=lambda x: x.timestamp)
        data = [
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "quote_volume": c.quote_volume or 0.0,
                "trades_count": c.trades_count or 0,
            }
            for c in candles
        ]

        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
        return df
