import { useCouncilState } from '@/stores/appStore'

export const CouncilPage = () => {
  const { councilMembers, activeDebateSession } = useCouncilState()

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Council</h1>
      <div className="border rounded p-3">
        <div className="font-medium mb-2">Members</div>
        <ul className="text-sm space-y-2">
          {councilMembers.map((m) => (
            <li key={m.memberId} className="flex items-center justify-between border-b last:border-b-0 py-1">
              <div>
                <div className="font-medium">{m.role}</div>
                <div className="opacity-70">{m.provider} • {m.model}</div>
              </div>
              <span className="opacity-70 capitalize">{m.currentStatus}</span>
            </li>
          ))}
          {councilMembers.length === 0 && (
            <li className="opacity-60">No members initialized yet</li>
          )}
        </ul>
      </div>

      <div className="border rounded p-3">
        <div className="font-medium mb-2">Active Debate</div>
        {activeDebateSession ? (
          <div className="text-sm">
            Stage: <span className="capitalize">{activeDebateSession.documentStage}</span>
          </div>
        ) : (
          <div className="text-sm opacity-70">No active debate</div>
        )}
      </div>
    </div>
  )
}

