/**
 * WebSocket-related constants for the frontend
 */

// Message types for frontend-backend communication
export const WS_MESSAGE_TYPES = {
	STATUS_UPDATE: 'status_update',
	COUNCIL_INITIALIZED: 'council_initialized',
	DOCUMENT_AUDIT_STARTED: 'document_audit_started', 
	DOCUMENT_AUDIT_COMPLETED: 'document_audit_completed',
	AUDIT_STARTED: 'audit_started',
	AUDIT_COMPLETED: 'audit_completed',
	ERROR: 'error',
	ERROR_OCCURRED: 'error_occurred',
	SYSTEM_ALERT: 'system_alert',
	HEARTBEAT: 'heartbeat',
	HEARTBEAT_ACK: 'heartbeat_ack',
	PING: 'ping',
	PONG: 'pong',
} as const

// WebSocket connection configuration
export const WS_CONFIG_DEFAULTS = {
	RECONNECT_INTERVAL: 3000,
	MAX_RECONNECT_ATTEMPTS: 10,
	HEARTBEAT_INTERVAL: 30000,
	MESSAGE_QUEUE_SIZE: 100,
	MAX_RECONNECT_DELAY: 30000,
	INITIAL_RECONNECT_DELAY: 100,
} as const

// Message priorities
export const MESSAGE_PRIORITIES = {
	LOW: 1,
	MEDIUM: 2, 
	HIGH: 3,
} as const

// Activity status mappings
export const ACTIVITY_STATUS_MAP = {
	reviewing: 'reviewing',
	responding: 'responding', 
	debating: 'debating',
	questioning: 'questioning',
	idle: 'idle',
} as const

// Provider mappings
export const PROVIDER_MAP = {
	openai: 'openai',
	anthropic: 'anthropic',
	google: 'google', 
	openrouter: 'openrouter',
} as const