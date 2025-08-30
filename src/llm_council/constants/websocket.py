"""WebSocket-related constants for the LLM Council platform."""

# WebSocket message types
WS_MESSAGE_TYPES = {
    "STATUS_UPDATE": "status_update",
    "COUNCIL_INITIALIZED": "council_initialized", 
    "DOCUMENT_AUDIT_STARTED": "document_audit_started",
    "DOCUMENT_AUDIT_COMPLETED": "document_audit_completed",
    "AUDIT_COMPLETED": "audit_completed",
    "ERROR": "error",
    "HEARTBEAT": "heartbeat",
    "PING": "ping",
    "PONG": "pong",
    "HEARTBEAT_ACK": "heartbeat_ack",
}

# WebSocket connection settings
WS_CLOSE_CODES = {
    "NORMAL": 1000,
    "MANUAL_RECONNECT": 1000,
    "SERVICE_DESTROYED": 1000,
}

# Default timeouts and intervals (in seconds)
WS_TIMEOUTS = {
    "HEARTBEAT_INTERVAL": 30.0,
    "RECONNECT_BASE_INTERVAL": 3.0,
    "MAX_RECONNECT_INTERVAL": 30.0,
    "MAX_RECONNECT_ATTEMPTS": 10,
    "MESSAGE_QUEUE_SIZE": 100,
}
