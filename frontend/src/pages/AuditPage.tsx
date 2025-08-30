import { CheckCircleIcon, ClockIcon, FileTextIcon, PlayIcon, XIcon } from 'lucide-react'
import { useState } from 'react'
import { usePipelineState } from '@/stores/appStore'

export const AuditPage = () => {
	const { pipelineProgress } = usePipelineState()
	const [activeTab, setActiveTab] = useState('research_brief')
	const [starting, setStarting] = useState(false)
	const [error, setError] = useState<string | null>(null)

	const documents = [
		{
			id: 'research_brief',
			name: 'Research Brief',
			fileName: 'RESEARCH_BRIEF.md',
			status: 'pending',
			completion: 0,
			description: 'Market research and problem validation',
			content: ''
		},
		{
			id: 'vision',
			name: 'Vision Document',
			fileName: 'VISION.md',
			status: 'pending',
			completion: 0,
			description: 'Product vision and MVP scope definition',
			content: ''
		},
		{
			id: 'prd',
			name: 'PRD',
			fileName: 'PRD.md',
			status: 'pending',
			completion: 0,
			description: 'Detailed requirements with acceptance criteria',
			content: ''
		},
		{
			id: 'architecture',
			name: 'Architecture',
			fileName: 'ARCHITECTURE.md',
			status: 'pending',
			completion: 0,
			description: 'Technical design and system architecture',
			content: ''
		},
		{
			id: 'implementation',
			name: 'Implementation Plan',
			fileName: 'IMPLEMENTATION_PLAN.md',
			status: 'pending',
			completion: 0,
			description: 'Task breakdown and development roadmap',
			content: ''
		},
	]

	const activeDocument = documents.find(doc => doc.id === activeTab)
	const nextDocument = documents.find((doc) => doc.status === 'in_progress') || documents.find((doc) => doc.status === 'pending')

	const startNextStage = async () => {
		if (!nextDocument) return

		setStarting(true)
		setError(null)
		try {
			const stage = nextDocument.id
			const projectId = 'local'
			const res = await fetch(`/api/projects/${projectId}/runs`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					docsPath: './docs',
					stage: stage,
					model: 'gpt-4o',
					council_debate: true,
					research_context: true,
				}),
			})
			if (!res.ok) throw new Error(`Failed to start ${nextDocument.name} (${res.status})`)
		} catch (e) {
			setError(e instanceof Error ? e.message : String(e))
		} finally {
			setStarting(false)
		}
	}

	const getStatusIcon = (status: string) => {
		switch (status) {
			case 'completed':
				return <CheckCircleIcon className="w-4 h-4 text-green-600" />
			case 'in_progress':
				return <ClockIcon className="w-4 h-4 text-blue-600 animate-pulse" />
			default:
				return <FileTextIcon className="w-4 h-4 text-gray-400" />
		}
	}

	const getTabColor = (status: string, isActive: boolean) => {
		if (isActive) {
			return 'border-b-blue-500 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400'
		}
		switch (status) {
			case 'completed':
				return 'hover:bg-green-50 dark:hover:bg-green-900/20 text-green-700 dark:text-green-300'
			case 'in_progress':
				return 'hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-700 dark:text-blue-300'
			default:
				return 'hover:bg-gray-50 dark:hover:bg-gray-900/20 text-gray-500'
		}
	}

	return (
		<div className="h-full flex flex-col">
			{/* Top Bar */}
			<div className="border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-4 py-3">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-lg font-semibold">Project Documents</h1>
						<p className="text-xs opacity-70">Research → Vision → Requirements → Architecture → Implementation</p>
					</div>
					{nextDocument && nextDocument.id === 'research_brief' && (
						<button
							onClick={startNextStage}
							type="button"
							disabled={starting}
							className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium transition-colors flex items-center gap-2"
						>
							{starting ? (
								<>
									Researching... <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
								</>
							) : (
								<>
									Start Research <PlayIcon className="w-3 h-3" />
								</>
							)}
						</button>
					)}
				</div>
			</div>

			{/* Tab Bar */}
			<div className="border-b dark:border-gray-700 bg-gray-100 dark:bg-gray-800">
				<div className="flex overflow-x-auto">
					{documents.map((doc) => (
						<button
							key={doc.id}
							type="button"
							onClick={() => setActiveTab(doc.id)}
							className={`flex items-center gap-2 px-4 py-3 border-b-2 border-transparent text-sm font-medium whitespace-nowrap transition-colors ${getTabColor(doc.status, activeTab === doc.id)}`}
						>
							{getStatusIcon(doc.status)}
							<span>{doc.name}</span>
							{doc.completion > 0 && (
								<span className="text-xs opacity-60">({doc.completion}%)</span>
							)}
							{activeTab === doc.id && doc.status !== 'pending' && (
								<XIcon className="w-3 h-3 opacity-50 hover:opacity-100" />
							)}
						</button>
					))}
				</div>
			</div>

			{/* Document Content */}
			<div className="flex-1 flex">
				{/* Document Editor/Viewer */}
				<div className="flex-1 flex flex-col">
					{activeDocument && (
						<>
							{/* Document Header */}
							<div className="border-b dark:border-gray-700 px-6 py-4 bg-white dark:bg-gray-800">
								<div className="flex items-center justify-between">
									<div>
										<h2 className="text-lg font-semibold flex items-center gap-2">
											{getStatusIcon(activeDocument.status)}
											{activeDocument.fileName}
										</h2>
										<p className="text-sm opacity-70">{activeDocument.description}</p>
									</div>
									{activeDocument.status === 'pending' && nextDocument?.id === activeDocument.id && (
										<button
											onClick={startNextStage}
											type="button"
											disabled={starting}
											className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded font-medium transition-colors"
										>
											Generate Document
										</button>
									)}
								</div>
							</div>

							{/* Document Content Area */}
							<div className="flex-1 bg-white dark:bg-gray-900">
								{activeDocument.content ? (
									<div className="h-full flex flex-col">
										<div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b dark:border-gray-700 text-xs font-mono text-gray-600 dark:text-gray-400">
											{activeDocument.fileName} • {activeDocument.completion}% complete
										</div>
										<div className="flex-1 p-6 overflow-auto">
											<pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed">
												{activeDocument.content}
											</pre>
										</div>
									</div>
								) : (
									<div className="h-full flex items-center justify-center">
										<div className="text-center space-y-6 max-w-md">
											<FileTextIcon className="w-20 h-20 mx-auto text-gray-300" />
											<div>
												<h3 className="text-xl font-semibold mb-2">{activeDocument.fileName}</h3>
												<p className="text-gray-600 dark:text-gray-400 mb-1">{activeDocument.description}</p>
												<p className="text-sm text-gray-500">Not generated yet</p>
											</div>
											
											{activeDocument.id === 'research_brief' && (
												<div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
													<h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Research Process:</h4>
													<ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1 text-left">
														<li>• Market intelligence gathering</li>
														<li>• Competitor analysis</li>
														<li>• Problem validation</li>
														<li>• Industry context research</li>
													</ul>
												</div>
											)}

											{activeDocument.id === 'vision' && (
												<div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-4">
													<h4 className="font-medium text-purple-900 dark:text-purple-100 mb-2">Vision Elements:</h4>
													<ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1 text-left">
														<li>• Product vision statement</li>
														<li>• Target user personas</li>
														<li>• MVP scope definition</li>
														<li>• Success metrics</li>
													</ul>
												</div>
											)}

											{nextDocument?.id === activeDocument.id && (
												<button
													onClick={startNextStage}
													type="button"
													disabled={starting}
													className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 mx-auto"
												>
													{starting ? (
														<>
															Generating... <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
														</>
													) : (
														<>
															Start {activeDocument.name} <PlayIcon className="w-4 h-4" />
														</>
													)}
												</button>
											)}
										</div>
									</div>
								)}
							</div>
						</>
					)}
				</div>

				{/* Sidebar - Council Status */}
				<div className="w-80 border-l dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex flex-col">
					<div className="border-b dark:border-gray-700 px-4 py-3">
						<h3 className="font-semibold">Council Activity</h3>
					</div>
					
					<div className="flex-1 p-4 overflow-auto">
						{error && (
							<div className="mb-4 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded p-3">
								{error}
							</div>
						)}

						{activeDocument.id === 'research_brief' ? (
							<div className="space-y-3">
								<div className="text-sm font-medium text-blue-600 mb-3">Research Phase Active</div>
								{[
									{ role: 'Research Agent', llm: 'Tavily + GPT-4', activity: 'Market intelligence gathering', status: 'active' },
									{ role: 'PM Auditor', llm: 'GPT-4o', activity: 'Problem validation', status: 'active' }
								].map((member) => (
									<div key={member.role} className="border rounded p-3 bg-white dark:bg-gray-800">
										<div className="flex items-center gap-2 mb-2">
											<div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
											<div className="font-medium text-sm">{member.role}</div>
										</div>
										<div className="text-xs opacity-60 mb-1">{member.llm}</div>
										<div className="text-xs opacity-80">{member.activity}</div>
									</div>
								))}
							</div>
						) : (
							<div className="space-y-3">
								<div className="text-sm text-gray-500 text-center py-4">
									Council members will activate when research begins
								</div>
							</div>
						)}
					</div>

					{/* Pipeline Status */}
					<div className="border-t dark:border-gray-700 p-4">
						<div className="border rounded p-3 bg-white dark:bg-gray-800">
							<div className="font-medium text-sm mb-2">Pipeline Status</div>
							<div className="text-xs opacity-70">
								Overall: <span className="capitalize font-medium">{pipelineProgress?.overallStatus ?? 'idle'}</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	)
}