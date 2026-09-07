"""
Repository layer providing clean CRUD operations for database models.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.models import BotLog, Candle, EquitySnapshot, Order, Trade


class TradeRepository:
    """Repository for managing Trade records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int = 50, offset: int = 0, is_paper: Optional[bool] = None) -> List[Trade]:
        stmt = select(Trade).order_by(desc(Trade.entry_time))
        if is_paper is not None:
            stmt = stmt.where(Trade.is_paper == is_paper)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_open_trades(self, symbol: Optional[str] = None, is_paper: Optional[bool] = None) -> List[Trade]:
        stmt = select(Trade).where(Trade.status == "OPEN")
        if symbol:
            stmt = stmt.where(Trade.symbol == symbol)
        if is_paper is not None:
            stmt = stmt.where(Trade.is_paper == is_paper)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, trade_id: str) -> Optional[Trade]:
        stmt = select(Trade).where(Trade.trade_id == trade_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, trade: Trade) -> Trade:
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade

    async def update(self, trade: Trade) -> Trade:
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade


class OrderRepository:
    """Repository for managing Order records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_client_id(self, client_order_id: str) -> Optional[Order]:
        stmt = select(Order).where(Order.client_order_id == client_order_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, limit: int = 50, is_paper: Optional[bool] = None) -> List[Order]:
        stmt = select(Order).order_by(desc(Order.created_at))
        if is_paper is not None:
            stmt = stmt.where(Order.is_paper == is_paper)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class EquityRepository:
    """Repository for managing Equity snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self) -> Optional[EquitySnapshot]:
        stmt = select(EquitySnapshot).order_by(desc(EquitySnapshot.timestamp)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_history(self, limit: int = 100) -> List[EquitySnapshot]:
        stmt = select(EquitySnapshot).order_by(desc(EquitySnapshot.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, snapshot: EquitySnapshot) -> EquitySnapshot:
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot


class CandleRepository:
    """Repository for managing Candlestick historical data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_candles(self, symbol: str, timeframe: str, limit: int = 100) -> List[Candle]:
        stmt = (
            select(Candle)
            .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
            .order_by(desc(Candle.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        candles = list(result.scalars().all())
        return list(reversed(candles))  # Chronological order

    async def insert_bulk(self, candles: List[Candle]):
        self.session.add_all(candles)
        await self.session.commit()


class LogRepository:
    """Repository for audit logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_log(self, level: str, event_type: str, message: str, details_json: Optional[str] = None):
        log_entry = BotLog(
            timestamp=datetime.now(timezone.utc),
            level=level,
            event_type=event_type,
            message=message,
            details_json=details_json,
        )
        self.session.add(log_entry)
        await self.session.commit()

    async def get_recent_logs(self, limit: int = 50) -> List[BotLog]:
        stmt = select(BotLog).order_by(desc(BotLog.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
