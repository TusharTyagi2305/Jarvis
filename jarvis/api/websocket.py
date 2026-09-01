import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from jarvis.api.events import WSEvent

logger = logging.getLogger("jarvis.api.websocket")

class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts real-time agent events.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast_event(self, event: WSEvent):
        if not self.active_connections:
            return
        
        event_dict = event.model_dump()
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(event_dict)
            except Exception as e:
                logger.warning(f"Error sending WebSocket event to client: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def broadcast_event_sync(self, event: WSEvent):
        import asyncio
        event_dict = event.model_dump()
        for connection in list(self.active_connections):
            try:
                # If running inside Starlette TestClient WebSocket, call send_json directly
                if hasattr(connection, "_websocket") or hasattr(connection, "send_json"):
                    res = connection.send_json(event_dict)
                    if asyncio.iscoroutine(res):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(res)
                        except RuntimeError:
                            asyncio.run(res)
            except Exception as e:
                logger.warning(f"Error sending event sync: {e}")

ws_manager = ConnectionManager()
