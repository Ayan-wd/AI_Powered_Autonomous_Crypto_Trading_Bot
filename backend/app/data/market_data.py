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


TIMEFRAME_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
}


def get_timeframe_seconds(timeframe: str) -> int:
    """Return period duration in seconds for a given timeframe."""
    return TIMEFRAME_SECONDS.get(timeframe.lower(), 60)


def is_candle_stale(
    latest_timestamp: datetime,
    timeframe: str,
    max_staleness_sec: Optional[int] = None,
) -> bool:
    """Check if the latest candle timestamp is older than the allowed staleness window."""
    if latest_timestamp.tzinfo is None:
        latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    allowed_sec = (
        max_staleness_sec
        if max_staleness_sec is not None
        else (get_timeframe_seconds(timeframe) * 2)
    )
    return (now_utc - latest_timestamp).total_seconds() > allowed_sec


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

        if session is not None and candle_models:
            from backend.app.database.repositories import CandleRepository

            repo = CandleRepository(session)
            await repo.upsert_many(candle_models)
            logger.info(f"Stored {len(candle_models)} validated candles for {symbol} ({timeframe})")

        return candle_models

    async def get_candles_dataframe(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        session: Optional[AsyncSession] = None,
        force_refresh: bool = False,
        max_staleness_sec: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Retrieve candles as a clean Pandas DataFrame with UTC DatetimeIndex.
        Guarantees temporal freshness: automatically fetches from exchange if local DB is stale,
        insufficient, or force_refresh is requested.
        """
        candles: List[Candle] = []
        is_stale = False
        if session and not force_refresh:
            stmt = (
                select(Candle)
                .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
                .order_by(desc(Candle.timestamp))
                .limit(limit)
            )
            res = await session.execute(stmt)
            candles = list(res.scalars().all())
            if candles:
                latest_ts = max(c.timestamp for c in candles)
                is_stale = is_candle_stale(latest_ts, timeframe, max_staleness_sec)

        if force_refresh or len(candles) < limit or is_stale:
            reason = (
                "force_refresh requested"
                if force_refresh
                else ("local DB candles stale" if is_stale else f"only {len(candles)} candles in DB")
            )
            logger.info(f"Fetching fresh {limit} candles for {symbol} ({timeframe}) from exchange ({reason})...")
            candles = await self.fetch_and_store_historical_candles(
                symbol=symbol, timeframe=timeframe, limit=limit, session=session
            )

        candles = sorted(candles, key=lambda x: x.timestamp)
        data = [
            {
                "timestamp": c.timestamp if c.timestamp.tzinfo else c.timestamp.replace(tzinfo=timezone.utc),
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
