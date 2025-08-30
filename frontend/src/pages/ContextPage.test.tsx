import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ContextPage } from './ContextPage'

// Mock ReactFlow components
vi.mock('reactflow', () => ({
  default: ({ children }: any) => <div data-testid="reactflow">{children}</div>,
  Controls: () => <div data-testid="reactflow-controls" />,
  Background: () => <div data-testid="reactflow-background" />,
  applyNodeChanges: vi.fn(),
  applyEdgeChanges: vi.fn()
}))

// Mock the WebSocket hook
vi.mock('@/hooks/useWebSocketConnection', () => ({
  useWebSocketConnection: vi.fn()
}))

// Mock fetch
global.fetch = vi.fn()

describe('ContextPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders with default graph view mode', () => {
    render(<ContextPage />)
    
    expect(screen.getByText('Context Builder')).toBeInTheDocument()
    expect(screen.getByTestId('reactflow')).toBeInTheDocument()
    expect(screen.getByText('Form')).toBeInTheDocument()
    expect(screen.getByText('Graph')).toBeInTheDocument()
  })

  it('loads context graph from localStorage on mount', () => {
    const mockGraphData = {
      nodes: [
        { id: 'n1', data: { label: 'Test Entity' }, position: { x: 100, y: 100 } }
      ],
      edges: [
        { id: 'e1', source: 'n1', target: 'n1' }
      ],
      confidence: 0.8
    }

    localStorage.setItem('llm-council.current-graph', JSON.stringify(mockGraphData))
    
    render(<ContextPage />)
    
    // Should show graph info panel
    expect(screen.getByText('Context Graph')).toBeInTheDocument()
    expect(screen.getByText('1 entities, 1 relationships')).toBeInTheDocument()
    expect(screen.getByText('Confidence: 80%')).toBeInTheDocument()
  })

  it('shows expand research button when graph data exists', () => {
    const mockGraphData = {
      nodes: [],
      edges: [],
      confidence: 0.7
    }

    localStorage.setItem('llm-council.current-graph', JSON.stringify(mockGraphData))
    
    render(<ContextPage />)
    
    expect(screen.getByRole('button', { name: /expand with research/i })).toBeInTheDocument()
  })

  it('calls research expansion API when expand button clicked', async () => {
    const mockGraphData = {
      nodes: [],
      edges: [],
      confidence: 0.7,
      entities: [],
      relationships: [],
      central_entity_id: '',
      confidence_score: 0.7
    }

    const mockExpandedResponse = {
      success: true,
      data: {
        nodes: [{ id: 'expanded', data: { label: 'Expanded Entity' } }],
        edges: [],
        confidence: 0.85
      }
    }

    localStorage.setItem('llm-council.current-graph', JSON.stringify(mockGraphData))
    
    ;(global.fetch as any).mockResolvedValueOnce({
      json: () => Promise.resolve(mockExpandedResponse)
    })

    render(<ContextPage />)
    
    const expandButton = screen.getByRole('button', { name: /expand with research/i })
    fireEvent.click(expandButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/ideas/expand-research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph: mockGraphData,
          focus_areas: [],
          max_insights: 10
        })
      })
    })
  })

  it('handles research expansion API errors', async () => {
    const mockGraphData = {
      nodes: [],
      edges: [],
      confidence: 0.7
    }

    localStorage.setItem('llm-council.current-graph', JSON.stringify(mockGraphData))
    
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(<ContextPage />)
    
    const expandButton = screen.getByRole('button', { name: /expand with research/i })
    fireEvent.click(expandButton)
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Research expansion failed:', expect.any(Error))
    })

    consoleSpy.mockRestore()
  })

  it('switches between form and graph view modes', () => {
    render(<ContextPage />)
    
    const formButton = screen.getByRole('button', { name: 'Form' })
    const graphButton = screen.getByRole('button', { name: 'Graph' })
    
    // Should start in graph mode
    expect(screen.getByTestId('reactflow')).toBeInTheDocument()
    
    // Switch to form mode
    fireEvent.click(formButton)
    expect(screen.getByText('Add your idea and click Generate Questions to begin.')).toBeInTheDocument()
    
    // Switch back to graph mode
    fireEvent.click(graphButton)
    expect(screen.getByTestId('reactflow')).toBeInTheDocument()
  })

  it('loads saved ideas from localStorage', () => {
    const mockSavedIdeas = [
      {
        id: 'idea1',
        title: 'Test Idea',
        text: 'A test idea for the app',
        questions: [],
        score: 85,
        updatedAt: Date.now()
      }
    ]

    localStorage.setItem('llm-council.context-ideas', JSON.stringify(mockSavedIdeas))
    
    render(<ContextPage />)
    
    expect(screen.getByText('Test Idea')).toBeInTheDocument()
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('handles localStorage errors gracefully', () => {
    // Mock localStorage.getItem to throw
    const originalGetItem = localStorage.getItem
    localStorage.getItem = vi.fn().mockImplementation(() => {
      throw new Error('Storage error')
    })
    
    // Should render without crashing
    expect(() => render(<ContextPage />)).not.toThrow()
    
    // Restore localStorage
    localStorage.getItem = originalGetItem
  })
})