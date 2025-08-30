import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { IdeaPage } from './IdeaPage'

// Mock the useConnectionState hook
vi.mock('@/stores/appStore', () => ({
  useConnectionState: () => ({
    connectionStatus: 'connected'
  })
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

// Mock fetch
global.fetch = vi.fn()

const renderIdeaPage = () => {
  return render(
    <BrowserRouter>
      <IdeaPage />
    </BrowserRouter>
  )
}

describe('IdeaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders the idea input form', () => {
    renderIdeaPage()
    
    expect(screen.getByText("What's your idea?")).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /generate context graph/i })).toBeInTheDocument()
  })

  it('shows character counter', () => {
    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'Test idea' } })
    
    expect(screen.getByText('9/1000')).toBeInTheDocument()
  })

  it('enables button when text is entered', () => {
    renderIdeaPage()
    
    const button = screen.getByRole('button', { name: /generate context graph/i })
    const textarea = screen.getByRole('textbox')
    
    // Initially disabled
    expect(button).toBeDisabled()
    
    // Enabled after text entry
    fireEvent.change(textarea, { target: { value: 'A great mobile app idea' } })
    expect(button).not.toBeDisabled()
  })

  it('generates project name correctly', () => {
    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'a mobile app for tracking water intake daily' } })
    
    // Project name should be first 3 words capitalized
    // This will be tested when the API call is made
    expect(textarea.value).toBe('a mobile app for tracking water intake daily')
  })

  it('calls context extraction API on button click', async () => {
    const mockResponse = {
      success: true,
      data: {
        nodes: [],
        edges: [],
        confidence: 0.8
      }
    }
    
    ;(global.fetch as any).mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse)
    })

    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button', { name: /generate context graph/i })
    
    fireEvent.change(textarea, { target: { value: 'A mobile app for tracking daily water intake' } })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/ideas/extract-context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'A mobile app for tracking daily water intake',
          project_name: 'A Mobile App',
          focus_areas: []
        })
      })
    })
  })

  it('stores graph data in localStorage and navigates on success', async () => {
    const mockGraphData = {
      nodes: [{ id: 'n1', data: { label: 'Test' } }],
      edges: [{ id: 'e1', source: 'n1', target: 'n1' }],
      confidence: 0.85
    }
    
    const mockResponse = {
      success: true,
      data: mockGraphData
    }
    
    ;(global.fetch as any).mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse)
    })

    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button', { name: /generate context graph/i })
    
    fireEvent.change(textarea, { target: { value: 'Test idea for graph generation' } })
    fireEvent.click(button)
    
    await waitFor(() => {
      const storedData = localStorage.getItem('llm-council.current-graph')
      expect(storedData).toBe(JSON.stringify(mockGraphData))
      expect(mockNavigate).toHaveBeenCalledWith('/context')
    })
  })

  it('handles API errors gracefully', async () => {
    const mockResponse = {
      success: false,
      error: 'Context extraction failed'
    }
    
    ;(global.fetch as any).mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse)
    })

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button', { name: /generate context graph/i })
    
    fireEvent.change(textarea, { target: { value: 'Test idea that will fail' } })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Context extraction failed:', 'Context extraction failed')
    })

    consoleSpy.mockRestore()
  })

  it('shows processing state during API call', async () => {
    ;(global.fetch as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        json: () => Promise.resolve({ success: true, data: {} })
      }), 100))
    )

    renderIdeaPage()
    
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button', { name: /generate context graph/i })
    
    fireEvent.change(textarea, { target: { value: 'Test idea for processing state' } })
    fireEvent.click(button)
    
    // Should show processing state
    expect(screen.getByText('Starting Research...')).toBeInTheDocument()
    expect(button).toBeDisabled()
    
    await waitFor(() => {
      expect(screen.queryByText('Starting Research...')).not.toBeInTheDocument()
    })
  })

  it('shows connection status warning when disconnected', () => {
    // Re-mock for disconnected state
    vi.doMock('@/stores/appStore', () => ({
      useConnectionState: () => ({
        connectionStatus: 'disconnected'
      })
    }))

    renderIdeaPage()
    
    expect(screen.getByText(/backend connection: disconnected/i)).toBeInTheDocument()
  })
})