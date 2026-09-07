"""
WebSocket Connection and Real-Time Event Broadcast Manager.
Enables low-latency streaming of market ticks, strategy signals, order fills, and equity updates to frontends.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from fastapi import WebSocket
from backend.app.core.logging import logger


class WebSocketManager:
    """Manages connected WebSocket dashboard clients and broadcasts real-time events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new client WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove disconnected client."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Any) -> None:
        """
        Broadcast structured JSON event to all connected dashboard clients.
        Example events: TICKER_UPDATE, CANDLE_CLOSED, SIGNAL_GENERATED, ORDER_EVENT, POSITION_UPDATE, EQUITY_UPDATE.
        """
        if not self.active_connections:
            return

        payload = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        dead_connections: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: Any) -> None:
        """Send message to a single specific client."""
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await websocket.send_json(payload)
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")


# Singleton WebSocket Manager
ws_manager = WebSocketManager()
