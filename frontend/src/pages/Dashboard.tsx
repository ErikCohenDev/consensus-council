import { useConnectionState, usePipelineState } from '@/stores/appStore'

export const Dashboard = () => {
  const { connectionStatus } = useConnectionState()
  const { pipelineProgress } = usePipelineState()

  const docs = pipelineProgress?.documents ?? []

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <div className="text-sm opacity-80">Connection: {connectionStatus}</div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="border rounded p-3">
          <div className="text-sm opacity-70">Documents</div>
          <div className="text-2xl font-semibold">{docs.length}</div>
        </div>
        <div className="border rounded p-3">
          <div className="text-sm opacity-70">Total Cost (USD)</div>
          <div className="text-2xl font-semibold">{pipelineProgress?.totalCostUsd ?? 0}</div>
        </div>
        <div className="border rounded p-3">
          <div className="text-sm opacity-70">Status</div>
          <div className="text-2xl font-semibold capitalize">{pipelineProgress?.overallStatus ?? 'idle'}</div>
        </div>
      </div>

      <div className="border rounded p-3">
        <div className="font-medium mb-2">Documents</div>
        <ul className="text-sm space-y-1">
          {docs.map((d) => (
            <li key={d.name} className="flex justify-between border-b last:border-b-0 py-1">
              <span>{d.name}</span>
              <span className="opacity-70 capitalize">{d.auditStatus}</span>
            </li>
          ))}
          {docs.length === 0 && <li className="opacity-60">No documents yet</li>}
        </ul>
      </div>
    </div>
  )
}

