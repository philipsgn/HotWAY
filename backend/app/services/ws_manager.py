"""
HotWAY WebSocket Connection Manager.
Manages customer tracking, driver PWA, and dispatcher channels with broadcast < 200ms.
"""

import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("hotway.ws_manager")


class ConnectionManager:
    """Manages active WebSocket connections grouped by channel or order_id."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.order_rooms: Dict[str, Set[WebSocket]] = {}
        self.driver_rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "default"):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug("WebSocket client connected to channel %s", channel)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for room in self.order_rooms.values():
            room.discard(websocket)
        for room in self.driver_rooms.values():
            room.discard(websocket)

    async def broadcast_json(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def disconnect_all(self):
        for connection in list(self.active_connections):
            try:
                await connection.close()
            except Exception:
                pass
        self.active_connections.clear()
        self.order_rooms.clear()
        self.driver_rooms.clear()


ws_manager = ConnectionManager()
