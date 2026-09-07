"""
WebSocket Streaming Route for Real-time Dashboard Live Feeds.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.api.websocket.ws_manager import ws_manager
from backend.app.core.logging import logger
from backend.app.execution.order_manager import order_manager

router = APIRouter(prefix="/ws", tags=["Real-time Streaming WebSockets"])


@router.websocket("/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    Live streaming WebSocket endpoint for continuous ticks, signals, orders, and equity updates.
    """
    await ws_manager.connect(websocket)

    try:
        # Send initial state snapshot upon connection
        pos = order_manager.get_active_position()
        balances = order_manager.get_account_balances()
        await ws_manager.send_personal(
            websocket,
            event_type="INITIAL_STATE",
            data={
                "active_position": pos,
                "balances": balances,
                "status": "CONNECTED",
            },
        )

        # Listen for client ping / subscriptions
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "PING")
            if msg_type == "PING":
                await ws_manager.send_personal(websocket, "PONG", {"server_time": data.get("client_time")})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client loop exception: {e}")
        ws_manager.disconnect(websocket)
