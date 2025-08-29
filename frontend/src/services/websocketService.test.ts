import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { getWebSocketService, destroyWebSocketService } from './websocketService'

// Minimal mock WebSocket that allows us to emit messages
class MockWebSocket {
  static instances: MockWebSocket[] = []
  public onopen: ((ev: Event) => void) | null = null
  public onclose: ((ev: CloseEvent) => void) | null = null
  public onerror: ((ev: Event) => void) | null = null
  public onmessage: ((ev: MessageEvent) => void) | null = null
  public readyState = 1 // OPEN
  public url: string

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    // Simulate async open
    setTimeout(() => this.onopen && this.onopen(new Event('open')), 0)
  }

  send(_data: string) {}
  close(_code?: number, _reason?: string) {
    this.readyState = 3 // CLOSED
    // Cast to satisfy typing without relying on CloseEvent constructor in jsdom
    this.onclose && this.onclose(new Event('close') as unknown as CloseEvent)
  }
  emit(data: unknown) {
    this.onmessage && this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
  }
}

describe('WebSocketService normalization', () => {
  beforeEach(() => {
    // @ts-expect-error override global for tests
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket
  })

  afterEach(() => {
    destroyWebSocketService()
    // @ts-expect-error cleanup
    global.WebSocket = undefined
    MockWebSocket.instances = []
  })

  it('maps status_update to NotificationMessage', async () => {
    const svc = getWebSocketService({ url: 'ws://test/ws' })

    let receivedType: string | null = null
    svc.onMessage((msg) => {
      receivedType = msg.type
    })

    // Emit backend-shaped status update
    const ws = MockWebSocket.instances[0]
    ws.emit({ type: 'status_update', status: { documents: [], overall_status: 'idle' } })

    await new Promise((r) => setTimeout(r, 10))
    expect(receivedType).toBe('status_update')
  })

  it('maps document_audit_started to audit_started', async () => {
    const svc = getWebSocketService({ url: 'ws://test/ws' })
    let receivedType: string | null = null
    svc.onMessage((msg) => {
      receivedType = msg.type
    })
    const ws = MockWebSocket.instances[0]
    ws.emit({ type: 'document_audit_started', document: { name: 'VISION.md' } })
    await new Promise((r) => setTimeout(r, 10))
    expect(receivedType).toBe('audit_started')
  })

  it('maps error to error_occurred', async () => {
    const svc = getWebSocketService({ url: 'ws://test/ws' })
    let receivedType: string | null = null
    svc.onMessage((msg) => {
      receivedType = msg.type
    })
    const ws = MockWebSocket.instances[0]
    ws.emit({ type: 'error', message: 'boom' })
    await new Promise((r) => setTimeout(r, 10))
    expect(receivedType).toBe('error_occurred')
  })
})
