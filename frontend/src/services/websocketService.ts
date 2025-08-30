/**
 * WebSocket service for real-time communication
 *
 * Provides a robust WebSocket connection with automatic reconnection,
 * message queuing, and proper error handling. Uses Zod for runtime
 * validation of incoming messages.
 */

import { parseWithSchema, Schemas } from '@shared/schemas/validation'
import type { NotificationMessage, WebSocketMessage } from '@shared/types/core'
import { WS_CONFIG_DEFAULTS, WS_MESSAGE_TYPES, MESSAGE_PRIORITIES } from '@/constants/websocket'

type MessageHandler = (message: NotificationMessage) => void
type ConnectionHandler = (connected: boolean) => void
type ErrorHandler = (error: Error) => void

interface WebSocketServiceConfig {
	url: string
	reconnectInterval: number
	maxReconnectAttempts: number
	heartbeatInterval: number
	messageQueueSize: number
}

const DEFAULT_CONFIG: WebSocketServiceConfig = {
	url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
	reconnectInterval: WS_CONFIG_DEFAULTS.RECONNECT_INTERVAL,
	maxReconnectAttempts: WS_CONFIG_DEFAULTS.MAX_RECONNECT_ATTEMPTS,
	heartbeatInterval: WS_CONFIG_DEFAULTS.HEARTBEAT_INTERVAL,
	messageQueueSize: WS_CONFIG_DEFAULTS.MESSAGE_QUEUE_SIZE,
}

export class WebSocketService {
	private ws: WebSocket | null = null
	private config: WebSocketServiceConfig
	private messageHandlers = new Set<MessageHandler>()
	private connectionHandlers = new Set<ConnectionHandler>()
	private errorHandlers = new Set<ErrorHandler>()

	private reconnectAttempts = 0
	private reconnectTimer: number | null = null
	private heartbeatTimer: number | null = null
	private messageQueue: string[] = []
	private isConnected = false
	private isDestroyed = false

	constructor(config: Partial<WebSocketServiceConfig> = {}) {
		this.config = { ...DEFAULT_CONFIG, ...config }
		this.connect()
	}

	/**
	 * Connect to WebSocket server
	 */
	private connect(): void {
		if (this.isDestroyed || this.isConnected) return

		try {
			console.log(`[WebSocket] Connecting to ${this.config.url}...`)
			this.ws = new WebSocket(this.config.url)

			this.ws.onopen = this.handleOpen.bind(this)
			this.ws.onclose = this.handleClose.bind(this)
			this.ws.onerror = this.handleError.bind(this)
			this.ws.onmessage = this.handleMessage.bind(this)
		} catch (error) {
			console.error('[WebSocket] Connection failed:', error)
			this.handleError(new Error(`Connection failed: ${error}`))
			this.scheduleReconnect()
		}
	}

	/**
	 * Handle WebSocket open event
	 */
	private handleOpen(): void {
		console.log('[WebSocket] Connected successfully')

		this.isConnected = true
		this.reconnectAttempts = 0
		this.clearReconnectTimer()

		// Send queued messages
		this.flushMessageQueue()

		// Start heartbeat
		this.startHeartbeat()

		// Notify connection handlers
		this.notifyConnectionHandlers(true)
	}

	/**
	 * Handle WebSocket close event
	 */
	private handleClose(event: CloseEvent): void {
		console.log(`[WebSocket] Connection closed: ${event.code} ${event.reason}`)

		this.isConnected = false
		this.clearHeartbeat()

		// Notify connection handlers
		this.notifyConnectionHandlers(false)

		// Schedule reconnect if not a clean close
		if (!this.isDestroyed && event.code !== 1000) {
			this.scheduleReconnect()
		}
	}

	/**
	 * Handle WebSocket error event
	 */
	private handleError(error: Event | Error): void {
		const errorMessage = error instanceof Error ? error.message : 'WebSocket error occurred'

		console.error('[WebSocket] Error:', errorMessage)

		const wsError = new Error(`WebSocket error: ${errorMessage}`)
		this.notifyErrorHandlers(wsError)

		this.isConnected = false
	}

	/**
	 * Handle incoming WebSocket message
	 */
	private handleMessage(event: MessageEvent): void {
		try {
			const raw = JSON.parse(event.data)

			// Normalize server events into NotificationMessage where possible
			const notification = this.normalizeToNotification(raw)

			if (notification) {
				// Validate final notification before dispatch
				try {
					const validated = parseWithSchema(Schemas.NotificationMessage, notification)
					this.notifyMessageHandlers(validated)
				} catch (validationError) {
					console.warn('[WebSocket] Notification validation failed:', validationError)
					// Still notify handlers with raw notification to avoid silent failures
					this.notifyMessageHandlers(notification)
				}
				return
			}

			// Fallback: if object matches generic WebSocketMessage, handle system cases
			if (this.isWebSocketMessage(raw)) {
				this.handleSystemMessage(raw as WebSocketMessage)
				return
			}

			// Unknown message shape
			console.log('[WebSocket] Unrecognized message shape:', raw)
		} catch (error) {
			console.error('[WebSocket] Failed to parse message:', error)
			this.notifyErrorHandlers(
				new Error(
					`Message parsing failed: ${error instanceof Error ? error.message : String(error)}`
				)
			)
		}
	}

	/**
	 * Best-effort normalization of backend events to NotificationMessage
	 */
	private normalizeToNotification(raw: unknown): NotificationMessage | null {
		if (!raw || typeof raw !== 'object') return null
		const obj = raw as Record<string, unknown>
		const type = typeof obj.type === 'string' ? obj.type : null

		if (!type) return null

		// Map backend event types to NotificationMessage types
		let mappedType: NotificationMessage['type']
		let priority: NotificationMessage['priority'] = 2
		let data: Record<string, unknown> = {}

		switch (type) {
			case WS_MESSAGE_TYPES.STATUS_UPDATE:
				mappedType = 'status_update'
				data = { ...(obj.status as object | undefined), raw: obj }
				priority = MESSAGE_PRIORITIES.LOW
				break
			case WS_MESSAGE_TYPES.COUNCIL_INITIALIZED:
				mappedType = 'status_update'
				data = { councilInitialized: true, members: obj.members }
				priority = MESSAGE_PRIORITIES.LOW
				break
			case WS_MESSAGE_TYPES.DOCUMENT_AUDIT_STARTED:
				mappedType = 'audit_started'
				data = { document: obj.document }
				priority = MESSAGE_PRIORITIES.MEDIUM
				break
			case WS_MESSAGE_TYPES.DOCUMENT_AUDIT_COMPLETED:
				mappedType = 'audit_completed'
				data = { document: obj.document, debate_result: obj.debate_result }
				priority = MESSAGE_PRIORITIES.MEDIUM
				break
			case WS_MESSAGE_TYPES.AUDIT_COMPLETED:
				mappedType = 'audit_completed'
				data = { ...(obj.status as object | undefined), raw: obj }
				priority = MESSAGE_PRIORITIES.MEDIUM
				break
			case WS_MESSAGE_TYPES.ERROR:
				mappedType = 'error_occurred'
				data = { message: obj.message ?? 'Unknown error', raw: obj }
				priority = MESSAGE_PRIORITIES.HIGH
				break
			case WS_MESSAGE_TYPES.HEARTBEAT:
			case WS_MESSAGE_TYPES.PING:
				// System messages aren't notifications
				return null
			default:
				mappedType = 'system_alert'
				data = { raw: obj }
				priority = MESSAGE_PRIORITIES.LOW
		}

		return {
			type: mappedType,
			data,
			timestamp: Date.now(),
			priority,
		}
	}

	/**
	 * Check if message matches WebSocketMessage shape
	 */
	private isWebSocketMessage(obj: unknown): obj is WebSocketMessage {
		return (
			obj != null &&
			typeof obj === 'object' &&
			'type' in obj &&
			typeof (obj as Record<string, unknown>).type === 'string'
		)
	}

	/**
	 * Handle system messages (heartbeat, etc.)
	 */
	private handleSystemMessage(message: WebSocketMessage): void {
		switch (message.type) {
			case WS_MESSAGE_TYPES.HEARTBEAT:
				this.sendMessage({ type: WS_MESSAGE_TYPES.HEARTBEAT_ACK, timestamp: Date.now() })
				break
			case WS_MESSAGE_TYPES.PING:
				this.sendMessage({ type: WS_MESSAGE_TYPES.PONG, timestamp: Date.now() })
				break
			default:
				console.log('[WebSocket] Unknown system message:', message.type)
		}
	}

	/**
	 * Send message to server
	 */
	public sendMessage(data: Record<string, unknown>): boolean {
		const message = JSON.stringify({
			...data,
			timestamp: Date.now(),
		})

		if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
			try {
				this.ws.send(message)
				return true
			} catch (error) {
				console.error('[WebSocket] Failed to send message:', error)
				this.queueMessage(message)
				return false
			}
		} else {
			this.queueMessage(message)
			return false
		}
	}

	/**
	 * Queue message for later sending
	 */
	private queueMessage(message: string): void {
		this.messageQueue.push(message)

		// Limit queue size
		if (this.messageQueue.length > this.config.messageQueueSize) {
			this.messageQueue.shift()
		}
	}

	/**
	 * Send all queued messages
	 */
	private flushMessageQueue(): void {
		while (this.messageQueue.length > 0 && this.isConnected) {
			const message = this.messageQueue.shift()
			if (message && this.ws?.readyState === WebSocket.OPEN) {
				try {
					this.ws.send(message)
				} catch (error) {
					console.error('[WebSocket] Failed to send queued message:', error)
					// Put it back at the front of the queue
					this.messageQueue.unshift(message)
					break
				}
			}
		}
	}

	/**
	 * Schedule reconnection attempt
	 */
	private scheduleReconnect(): void {
		if (this.isDestroyed || this.reconnectAttempts >= this.config.maxReconnectAttempts) {
			console.error('[WebSocket] Max reconnect attempts reached')
			return
		}

		this.reconnectAttempts++

		const delay = Math.min(
			this.config.reconnectInterval * 2 ** (this.reconnectAttempts - 1),
			WS_CONFIG_DEFAULTS.MAX_RECONNECT_DELAY
		)

		console.log(`[WebSocket] Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`)

		this.reconnectTimer = window.setTimeout(() => {
			if (!this.isDestroyed) {
				this.connect()
			}
		}, delay)
	}

	/**
	 * Clear reconnect timer
	 */
	private clearReconnectTimer(): void {
		if (this.reconnectTimer) {
			clearTimeout(this.reconnectTimer)
			this.reconnectTimer = null
		}
	}

	/**
	 * Start heartbeat mechanism
	 */
	private startHeartbeat(): void {
		this.clearHeartbeat()

		this.heartbeatTimer = window.setInterval(() => {
			if (this.isConnected) {
				this.sendMessage({ type: WS_MESSAGE_TYPES.PING })
			}
		}, this.config.heartbeatInterval)
	}

	/**
	 * Clear heartbeat timer
	 */
	private clearHeartbeat(): void {
		if (this.heartbeatTimer) {
			clearInterval(this.heartbeatTimer)
			this.heartbeatTimer = null
		}
	}

	/**
	 * Notify message handlers
	 */
	private notifyMessageHandlers(message: NotificationMessage): void {
		this.messageHandlers.forEach((handler) => {
			try {
				handler(message)
			} catch (error) {
				console.error('[WebSocket] Message handler error:', error)
			}
		})
	}

	/**
	 * Notify connection handlers
	 */
	private notifyConnectionHandlers(connected: boolean): void {
		this.connectionHandlers.forEach((handler) => {
			try {
				handler(connected)
			} catch (error) {
				console.error('[WebSocket] Connection handler error:', error)
			}
		})
	}

	/**
	 * Notify error handlers
	 */
	private notifyErrorHandlers(error: Error): void {
		this.errorHandlers.forEach((handler) => {
			try {
				handler(error)
			} catch (error) {
				console.error('[WebSocket] Error handler error:', error)
			}
		})
	}

	/**
	 * Subscribe to messages
	 */
	public onMessage(handler: MessageHandler): () => void {
		this.messageHandlers.add(handler)
		return () => this.messageHandlers.delete(handler)
	}

	/**
	 * Subscribe to connection changes
	 */
	public onConnection(handler: ConnectionHandler): () => void {
		this.connectionHandlers.add(handler)
		return () => this.connectionHandlers.delete(handler)
	}

	/**
	 * Subscribe to errors
	 */
	public onError(handler: ErrorHandler): () => void {
		this.errorHandlers.add(handler)
		return () => this.errorHandlers.delete(handler)
	}

	/**
	 * Subscribe to specific event types
	 */
	public subscribe(eventType: string, handler: MessageHandler): () => void {
		const filteredHandler: MessageHandler = (message) => {
			if (message.type === eventType) {
				handler(message)
			}
		}

		return this.onMessage(filteredHandler)
	}

	/**
	 * Get connection status
	 */
	public getConnectionStatus(): {
		isConnected: boolean
		reconnectAttempts: number
		queuedMessages: number
	} {
		return {
			isConnected: this.isConnected,
			reconnectAttempts: this.reconnectAttempts,
			queuedMessages: this.messageQueue.length,
		}
	}

	/**
	 * Force reconnection
	 */
	public reconnect(): void {
		console.log('[WebSocket] Manual reconnection triggered')

		this.isConnected = false
		this.reconnectAttempts = 0

		if (this.ws) {
			this.ws.close(1000, 'Manual reconnect')
		}

		this.clearReconnectTimer()
		this.clearHeartbeat()

		// Reconnect after a short delay
		setTimeout(() => this.connect(), WS_CONFIG_DEFAULTS.INITIAL_RECONNECT_DELAY)
	}

	/**
	 * Destroy the service
	 */
	public destroy(): void {
		console.log('[WebSocket] Destroying service')

		this.isDestroyed = true
		this.isConnected = false

		this.clearReconnectTimer()
		this.clearHeartbeat()

		if (this.ws) {
			this.ws.close(1000, 'Service destroyed')
			this.ws = null
		}

		this.messageHandlers.clear()
		this.connectionHandlers.clear()
		this.errorHandlers.clear()
		this.messageQueue = []
	}
}

// Singleton instance
let webSocketService: WebSocketService | null = null

/**
 * Get or create WebSocket service instance
 */
export const getWebSocketService = (config?: Partial<WebSocketServiceConfig>): WebSocketService => {
	if (!webSocketService || config) {
		webSocketService = new WebSocketService(config)
	}
	return webSocketService
}

/**
 * Destroy the WebSocket service instance
 */
export const destroyWebSocketService = (): void => {
	if (webSocketService) {
		webSocketService.destroy()
		webSocketService = null
	}
}
