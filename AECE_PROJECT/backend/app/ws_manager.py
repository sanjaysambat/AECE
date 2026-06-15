import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    """
    Very small websocket manager for demo-grade real-time updates.
    Broadcasts are global (all connected clients receive the same events).
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._weights_by_connection: dict[WebSocket, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            self._weights_by_connection[websocket] = {}

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
            self._weights_by_connection.pop(websocket, None)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        # Send concurrently; remove failing connections.
        async with self._lock:
            connections = list(self._connections)

        if not connections:
            return

        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_json(payload)
            except WebSocketDisconnect:
                await self.disconnect(ws)
            except Exception:
                await self.disconnect(ws)

        await asyncio.gather(*[_send(ws) for ws in connections], return_exceptions=True)

    def connected_count(self) -> int:
        return len(self._connections)

    async def set_weights(self, websocket: WebSocket, weights: dict[str, Any]) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._weights_by_connection[websocket] = dict(weights)

    def get_weights(self, websocket: WebSocket) -> dict[str, Any]:
        return self._weights_by_connection.get(websocket, {})

