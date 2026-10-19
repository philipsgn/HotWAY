"""
WebSocket Endpoints for Real-Time Telemetry & Tracking.
Latency budget: < 200 ms broadcast latency.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.ws_manager import ws_manager

logger = logging.getLogger("hotway.ws")
router = APIRouter()


@router.websocket("/ws/tracking/{order_id}")
async def websocket_tracking(websocket: WebSocket, order_id: str):
    """Customer real-time order tracking WebSocket stream."""
    await ws_manager.connect(websocket, channel=f"order:{order_id}")
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process client ping
            await websocket.send_json({
                "event": "PONG",
                "order_id": order_id,
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/driver/{driver_id}")
async def websocket_driver(websocket: WebSocket, driver_id: str):
    """Shipper PWA GPS emit and dispatch instruction stream."""
    await ws_manager.connect(websocket, channel=f"driver:{driver_id}")
    try:
        while True:
            payload = await websocket.receive_json()
            # Handle DRIVER_GPS_EMIT
            event_type = payload.get("event")
            if event_type == "DRIVER_GPS_EMIT":
                # Broadcast update to customer channel
                await ws_manager.broadcast_json({
                    "event": "SHIPPER_TELEMETRY_UPDATE",
                    "driver_id": driver_id,
                    "order_id": payload.get("order_id"),
                    "lat": payload.get("lat"),
                    "lon": payload.get("lon"),
                    "speed_kmh": payload.get("speed_kmh", 0.0),
                    "current_temp_c": payload.get("current_temp_c", 80.0),
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/dispatcher")
async def websocket_dispatcher(websocket: WebSocket):
    """Dispatcher live dashboard broadcast channel."""
    await ws_manager.connect(websocket, channel="dispatcher")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
