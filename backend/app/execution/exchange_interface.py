"""
Exchange abstraction interface.
Defines the uniform protocol for all exchange adapters (Binance, Paper, or future exchanges),
ensuring zero coupling between exchange-specific APIs and the strategy/ML engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TickerData(BaseModel):
    symbol: str
    price: float
    bid_price: float
    ask_price: float
    volume_24h: float
    price_change_24h_pct: float
    timestamp: int


class OrderBookData(BaseModel):
    symbol: str
    bids: List[List[float]]  # [[price, qty], ...]
    asks: List[List[float]]
    timestamp: int


class ExchangeInterface(ABC):
    """Abstract Base Class for Crypto Exchange Implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connections, sessions, or credentials."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> TickerData:
        """Fetch latest ticker price and 24h stats."""
        pass

    @abstractmethod
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV candlestick data.
        Returns list of dicts with keys: timestamp, open, high, low, close, volume, quote_volume, trades_count, is_closed.
        """
        pass

    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 20) -> OrderBookData:
        """Fetch current order book depth."""
        pass

    @abstractmethod
    async def get_account_balance(self) -> Dict[str, float]:
        """Fetch free and locked asset balances."""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch active open orders."""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        order_type: str,  # MARKET, LIMIT, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit an order to the exchange."""
        pass

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an open order."""
        pass

    @abstractmethod
    async def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Query execution status of an existing order."""
        pass
