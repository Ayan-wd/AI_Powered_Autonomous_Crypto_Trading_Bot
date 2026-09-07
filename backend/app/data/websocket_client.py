"""
Real-time WebSocket client for live candlestick and ticker feeds.
Supports automatic reconnection, exponential backoff, and candle-close callbacks.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import websockets
from backend.app.core.config import settings
from backend.app.core.logging import logger


class BinanceWebSocketClient:
    """Async WebSocket client for Binance Spot feeds."""

    def __init__(
        self,
        symbol: str = "btcusdt",
        timeframe: str = "15m",
        on_candle_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        testnet: Optional[bool] = None,
    ):
        self.symbol = symbol.lower()
        self.timeframe = timeframe
        self.on_candle_close = on_candle_close
        self.testnet = testnet if testnet is not None else settings.BINANCE_TESTNET

        # Binance public streams work identically for real-time market data
        self.ws_base_url = "wss://stream.binance.com:9443/ws"

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.latest_ticker: Dict[str, Any] = {}
        self.latest_candle: Dict[str, Any] = {}

    @property
    def stream_name(self) -> str:
        return f"{self.symbol}@kline_{self.timeframe}"

    async def start(self) -> None:
        """Start the WebSocket listener in the background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"WebSocket client started for stream: {self.stream_name}")

    async def stop(self) -> None:
        """Gracefully terminate WebSocket listener."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket client stopped.")

    async def _listen_loop(self) -> None:
        """Persistent connection loop with exponential backoff."""
        retry_delay = 1.0
        max_delay = 60.0

        while self._running:
            url = f"{self.ws_base_url}/{self.stream_name}"
            try:
                logger.info(f"Connecting to WebSocket: {url}")
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"WebSocket connected successfully to {self.stream_name}")
                    retry_delay = 1.0  # Reset on successful connection

                    while self._running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        await self._process_message(data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                logger.warning(
                    f"WebSocket disconnected ({e}). Reconnecting in {retry_delay:.1f}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process incoming kline message."""
        if "k" not in data:
            return

        k = data["k"]
        candle = {
            "symbol": k["s"],
            "timeframe": k["i"],
            "timestamp": int(k["t"]),
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
            "is_closed": bool(k["x"]),
            "close_time": int(k["T"]),
        }
        self.latest_candle = candle

        # If candle closed, trigger the callback for strategy execution
        if candle["is_closed"] and self.on_candle_close:
            try:
                if asyncio.iscoroutinefunction(self.on_candle_close):
                    await self.on_candle_close(candle)
                else:
                    self.on_candle_close(candle)
            except Exception as e:
                logger.error(f"Error in on_candle_close callback: {e}")
