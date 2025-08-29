import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useWebSocketConnection } from './useWebSocketConnection'
import { usePipelineState } from '@/stores/appStore'

// Mock the WebSocket service to avoid real sockets
type Handler<T> = (arg: T) => void
const handlers = {
  message: new Set<Handler<any>>(),
  connection: new Set<Handler<boolean>>(),
  error: new Set<Handler<Error>>(),
}

vi.mock('@/services/websocketService', () => {
  const service = {
    onMessage: (h: Handler<any>) => {
      handlers.message.add(h)
      return () => handlers.message.delete(h)
    },
    onConnection: (h: Handler<boolean>) => {
      handlers.connection.add(h)
      return () => handlers.connection.delete(h)
    },
    onError: (h: Handler<Error>) => {
      handlers.error.add(h)
      return () => handlers.error.delete(h)
    },
    getConnectionStatus: () => ({ isConnected: true, reconnectAttempts: 0, queuedMessages: 0 }),
    reconnect: () => {},
    destroy: () => {},
  }
  return {
    getWebSocketService: () => service,
    destroyWebSocketService: () => {},
    __emit: {
      message: (m: any) => handlers.message.forEach((h) => h(m)),
      connection: (c: boolean) => handlers.connection.forEach((h) => h(c)),
      error: (e: Error) => handlers.error.forEach((h) => h(e)),
    },
  }
})

// eslint-disable-next-line @typescript-eslint/consistent-type-definitions
type NotificationMessage = {
  type: string
  data: Record<string, unknown>
  timestamp: number
  priority: 1 | 2 | 3 | 4
}

const TestComp = () => {
  useWebSocketConnection()
  const { pipelineProgress, isAuditRunning } = usePipelineState()
  return (
    <div>
      <span data-testid="status">{pipelineProgress?.overallStatus ?? 'none'}</span>
      <span data-testid="running">{String(isAuditRunning)}</span>
    </div>
  )
}

describe('useWebSocketConnection', () => {
  beforeEach(() => {
    // Reset handlers between tests
    handlers.message.clear()
    handlers.connection.clear()
    handlers.error.clear()
  })

  afterEach(() => {
    handlers.message.clear()
    handlers.connection.clear()
    handlers.error.clear()
  })

  it('updates pipeline status on status_update', async () => {
    const wsModule = await import('@/services/websocketService')
    render(<TestComp />)

    const msg: NotificationMessage = {
      type: 'status_update',
      data: {
        documents: [],
        council_members: [],
        current_debate_round: null,
        research_progress: [],
        total_cost_usd: 0,
        execution_time: 0,
        overall_status: 'running',
      },
      timestamp: Date.now(),
      priority: 1,
    }

    ;(wsModule as any).__emit.message(msg)

    // Let state update
    await new Promise((r) => setTimeout(r, 10))
    expect(screen.getByTestId('status').textContent).toBe('running')
  })

  it('toggles isAuditRunning on audit events', async () => {
    const wsModule = await import('@/services/websocketService')
    render(<TestComp />)

    const started: NotificationMessage = { type: 'audit_started', data: {}, timestamp: Date.now(), priority: 2 }
    const completed: NotificationMessage = {
      type: 'audit_completed',
      data: {
        documents: [],
        council_members: [],
        current_debate_round: null,
        research_progress: [],
        total_cost_usd: 0,
        execution_time: 0,
        overall_status: 'completed',
      },
      timestamp: Date.now(),
      priority: 2,
    }

    ;(wsModule as any).__emit.message(started)
    await new Promise((r) => setTimeout(r, 10))
    expect(screen.getByTestId('running').textContent).toBe('true')

    ;(wsModule as any).__emit.message(completed)
    await new Promise((r) => setTimeout(r, 10))
    expect(screen.getByTestId('running').textContent).toBe('false')
    expect(screen.getByTestId('status').textContent).toBe('completed')
  })
})

