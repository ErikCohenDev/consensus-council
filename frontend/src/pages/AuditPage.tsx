import { useState } from 'react'
import { usePipelineState } from '@/stores/appStore'

export const AuditPage = () => {
  const { pipelineProgress } = usePipelineState()
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startAudit = async () => {
    setStarting(true)
    setError(null)
    try {
      // Simple trigger using dev proxy to backend
      const params = new URLSearchParams({ docs_path: './docs' })
      const res = await fetch(`/api/start_audit?${params.toString()}`, { method: 'POST' })
      if (!res.ok) throw new Error(`Failed to start audit (${res.status})`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Audit</h1>
      <button
        onClick={startAudit}
        disabled={starting}
        className="px-3 py-2 border rounded disabled:opacity-50"
      >
        {starting ? 'Starting…' : 'Start Audit'}
      </button>
      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="border rounded p-3">
        <div className="font-medium mb-2">Current Status</div>
        <div className="text-sm">
          Overall: <span className="capitalize">{pipelineProgress?.overallStatus ?? 'idle'}</span>
        </div>
      </div>
    </div>
  )
}

