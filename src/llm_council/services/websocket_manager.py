"""WebSocket connection management for real-time UI updates."""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time updates with optional scoping."""

    def __init__(self):
        # Each item: { "ws": WebSocket, "filters": {"projectId": str|None, "runId": str|None} }
        self.active_connections: List[Dict[str, Any]] = []

    async def connect(
        self, websocket: WebSocket, filters: Optional[Dict[str, Optional[str]]] = None
    ):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(
            {"ws": websocket, "filters": filters or {"projectId": None, "runId": None}}
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.active_connections = [
            c for c in self.active_connections if c.get("ws") is not websocket
        ]

    async def send_update(self, message: Dict[str, Any]):
        """Send update to all connected clients, honoring optional project/run filters."""
        msg_proj = message.get("project_id") or message.get("projectId")
        msg_run = (
            message.get("run_id") or message.get("runId") or message.get("audit_id")
        )
        disconnected: List[Dict[str, Any]] = []
        for entry in self.active_connections:
            ws = entry["ws"]
            flt = entry.get("filters") or {}
            f_proj = flt.get("projectId")
            f_run = flt.get("runId")
            # deliver if no filters, or filters match message
            deliver = True
            if f_proj and msg_proj and f_proj != msg_proj:
                deliver = False
            if f_run and msg_run and f_run != msg_run:
                deliver = False
            if not deliver:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(entry)

        # Clean up disconnected clients
        for entry in disconnected:
            try:
                self.active_connections.remove(entry)
            except ValueError:
                pass

