import { usePipelineState } from '@/stores/appStore'

export const PipelinePage = () => {
	const { pipelineProgress, currentAuditStage, isAuditRunning } = usePipelineState()
	return (
		<div className="space-y-4">
			<h1 className="text-xl font-semibold">Pipeline</h1>
			<div className="text-sm opacity-80">
				Running: {String(isAuditRunning)} • Current Stage: {currentAuditStage ?? '-'}
			</div>
			<pre className="text-xs border rounded p-3 overflow-auto bg-gray-50 dark:bg-gray-900">
				{JSON.stringify(pipelineProgress, null, 2)}
			</pre>
		</div>
	)
}
