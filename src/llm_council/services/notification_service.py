"""Notification service for real-time UI updates.

Handles WebSocket connections, event broadcasting, and maintains
separation between business logic and presentation concerns.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

from ..interfaces import IEventSubscriber, INotificationService


logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications that can be sent."""
    STATUS_UPDATE = "status_update"
    AUDIT_STARTED = "audit_started"
    AUDIT_COMPLETED = "audit_completed"
    DEBATE_STARTED = "debate_started"
    DEBATE_ROUND_COMPLETED = "debate_round_completed"
    CONSENSUS_REACHED = "consensus_reached"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_ALERT = "system_alert"


@dataclass
class NotificationMessage:
    """Structured notification message."""
    type: NotificationType
    data: Dict[str, Any]
    timestamp: float
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical


class WebSocketConnection:
    """Wrapper for WebSocket connections with metadata."""

    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.subscriptions: Set[str] = set()
        self.is_active = True

    async def send(self, message: NotificationMessage) -> bool:
        """Send message to this connection."""
        try:
            message_dict = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp,
                "priority": message.priority
            }

            await self.websocket.send_text(json.dumps(message_dict))
            return True

        except WebSocketDisconnect:
            self.is_active = False
            return False
        except (ConnectionError, OSError, ValueError) as e:
            logger.error("Failed to send message to %s: %s", self.client_id, e)
            self.is_active = False
            return False

    def subscribe_to(self, event_type: str) -> None:
        """Subscribe to specific event type."""
        self.subscriptions.add(event_type)

    def unsubscribe_from(self, event_type: str) -> None:
        """Unsubscribe from event type."""
        self.subscriptions.discard(event_type)

    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if subscribed to event type."""
        return event_type in self.subscriptions or len(self.subscriptions) == 0


class NotificationService(INotificationService):
    """Service for managing real-time notifications to UI clients."""

    def __init__(self, event_subscriber: IEventSubscriber):
        self._event_subscriber = event_subscriber
        self._connections: Dict[str, WebSocketConnection] = {}
        self._message_history: List[NotificationMessage] = []
        self._max_history_size = 100

        # Note: _setup_event_subscriptions() is async but called from __init__
        # In practice, this would be handled during service startup
        # self._setup_event_subscriptions()

        logger.info("NotificationService initialized")

    async def _setup_event_subscriptions(self) -> None:
        """Set up subscriptions to system events."""
        event_mappings = {
            "audit_started": NotificationType.AUDIT_STARTED,
            "audit_completed": NotificationType.AUDIT_COMPLETED,
            "audit_failed": NotificationType.ERROR_OCCURRED,
            "debate_session_started": NotificationType.DEBATE_STARTED,
            "debate_round_completed": NotificationType.DEBATE_ROUND_COMPLETED,
            "debate_session_completed": NotificationType.CONSENSUS_REACHED,
            "debate_session_failed": NotificationType.ERROR_OCCURRED,
        }

        for event_type, notification_type in event_mappings.items():
            await self._event_subscriber.subscribe(
                event_type,
                lambda data, ntype=notification_type: self._handle_system_event(ntype, data)
            )

    async def _handle_system_event(self, notification_type: NotificationType, data: Dict[str, Any]) -> None:
        """Handle system events and convert them to notifications."""
        message = NotificationMessage(
            type=notification_type,
            data=data,
            timestamp=datetime.now().timestamp(),
            priority=2 if notification_type == NotificationType.ERROR_OCCURRED else 1
        )

        await self._broadcast_message(message)

    async def connect_client(self, websocket: WebSocket, client_id: str) -> WebSocketConnection:
        """Connect a new WebSocket client."""
        await websocket.accept()

        connection = WebSocketConnection(websocket, client_id)
        self._connections[client_id] = connection

        # Send recent message history to new client
        await self._send_history_to_client(connection)

        logger.info("Client %s connected (%d total)", client_id, len(self._connections))

        # Send welcome message
        welcome_message = NotificationMessage(
            type=NotificationType.SYSTEM_ALERT,
            data={"message": "Connected to LLM Council platform", "client_id": client_id},
            timestamp=datetime.now().timestamp()
        )
        await connection.send(welcome_message)

        return connection

    def disconnect_client(self, client_id: str) -> None:
        """Disconnect a WebSocket client."""
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(f"Client {client_id} disconnected ({len(self._connections)} remaining)")

    async def notify_status_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send status change notification to all clients."""
        message = NotificationMessage(
            type=NotificationType.STATUS_UPDATE,
            data={"event_type": event_type, **data},
            timestamp=datetime.now().timestamp()
        )

        await self._broadcast_message(message)

    async def notify_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Send error notification to all clients."""
        message = NotificationMessage(
            type=NotificationType.ERROR_OCCURRED,
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            },
            timestamp=datetime.now().timestamp(),
            priority=3  # High priority for errors
        )

        await self._broadcast_message(message)

    async def notify_audit_progress(
        self,
        stage: str,
        progress: float,
        current_step: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send audit progress notification."""
        message = NotificationMessage(
            type=NotificationType.STATUS_UPDATE,
            data={
                "event_type": "audit_progress",
                "stage": stage,
                "progress": progress,
                "current_step": current_step,
                "details": details or {}
            },
            timestamp=datetime.now().timestamp()
        )

        await self._broadcast_message(message)

    async def notify_debate_update(
        self,
        session_id: str,
        round_number: int,
        participants: List[str],
        consensus_points: List[str],
        disagreements: List[str]
    ) -> None:
        """Send debate update notification."""
        message = NotificationMessage(
            type=NotificationType.DEBATE_ROUND_COMPLETED,
            data={
                "session_id": session_id,
                "round_number": round_number,
                "participants": participants,
                "consensus_points": consensus_points,
                "disagreements": disagreements
            },
            timestamp=datetime.now().timestamp()
        )

        await self._broadcast_message(message)

    async def _broadcast_message(self, message: NotificationMessage) -> None:
        """Broadcast message to all connected clients."""
        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history_size:
            self._message_history.pop(0)

        # Send to all active connections
        disconnected_clients = []

        for client_id, connection in self._connections.items():
            if not connection.is_active:
                disconnected_clients.append(client_id)
                continue

            # Check subscription filter
            if connection.is_subscribed_to(message.type.value):
                success = await connection.send(message)
                if not success:
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect_client(client_id)

        if disconnected_clients:
            logger.info(f"Cleaned up {len(disconnected_clients)} disconnected clients")

    async def _send_history_to_client(self, connection: WebSocketConnection) -> None:
        """Send recent message history to a newly connected client."""
        # Send last 10 messages
        recent_messages = self._message_history[-10:] if self._message_history else []

        for message in recent_messages:
            if connection.is_subscribed_to(message.type.value):
                await connection.send(message)

    async def subscribe_client(self, client_id: str, event_types: List[str]) -> bool:
        """Subscribe client to specific event types."""
        if client_id not in self._connections:
            return False

        connection = self._connections[client_id]
        for event_type in event_types:
            connection.subscribe_to(event_type)

        logger.debug(f"Client {client_id} subscribed to {event_types}")
        return True

    async def unsubscribe_client(self, client_id: str, event_types: List[str]) -> bool:
        """Unsubscribe client from specific event types."""
        if client_id not in self._connections:
            return False

        connection = self._connections[client_id]
        for event_type in event_types:
            connection.unsubscribe_from(event_type)

        logger.debug(f"Client {client_id} unsubscribed from {event_types}")
        return True

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get information about connected clients."""
        return [
            {
                "client_id": connection.client_id,
                "connected_at": connection.connected_at.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "is_active": connection.is_active
            }
            for connection in self._connections.values()
        ]

    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history."""
        recent_messages = self._message_history[-limit:] if self._message_history else []
        return [
            {
                "type": msg.type.value,
                "data": msg.data,
                "timestamp": msg.timestamp,
                "priority": msg.priority
            }
            for msg in recent_messages
        ]

    async def send_system_alert(
        self,
        message: str,
        priority: int = 2,
        target_clients: Optional[List[str]] = None
    ) -> None:
        """Send system alert message."""
        alert_message = NotificationMessage(
            type=NotificationType.SYSTEM_ALERT,
            data={"message": message, "priority": priority},
            timestamp=datetime.now().timestamp(),
            priority=priority
        )

        if target_clients:
            # Send to specific clients
            for client_id in target_clients:
                if client_id in self._connections:
                    connection = self._connections[client_id]
                    await connection.send(alert_message)
        else:
            # Broadcast to all clients
            await self._broadcast_message(alert_message)

    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        return {
            "connected_clients": len(self._connections),
            "active_connections": sum(1 for c in self._connections.values() if c.is_active),
            "message_history_size": len(self._message_history),
            "total_subscriptions": sum(len(c.subscriptions) for c in self._connections.values())
        }


__all__ = [
    "NotificationService",
    "NotificationMessage",
    "NotificationType",
    "WebSocketConnection"
]
