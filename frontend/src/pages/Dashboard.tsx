import { useState } from 'react'
import { LightbulbIcon, ArrowRightIcon, SearchIcon, FileTextIcon, UsersIcon, RocketIcon } from 'lucide-react'
import { useConnectionState, usePipelineState } from '@/stores/appStore'

export const Dashboard = () => {
	const { connectionStatus } = useConnectionState()
	const { pipelineProgress } = usePipelineState()
	const [ideaText, setIdeaText] = useState('')
	const [projectName, setProjectName] = useState('')
	const [currentStep, setCurrentStep] = useState<'idea' | 'processing' | 'complete'>('idea')
	const [isProcessing, setIsProcessing] = useState(false)

	const generateProjectName = (idea: string) => {
		// Simple project name generation from idea
		const words = idea.split(' ').slice(0, 3)
		return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
	}

	const startFullJourney = async () => {
		if (!ideaText.trim()) return
		
		setIsProcessing(true)
		setCurrentStep('processing')
		
		const generatedName = projectName || generateProjectName(ideaText)
		setProjectName(generatedName)

		try {
			// Start comprehensive research and document generation
			const response = await fetch('/api/audits', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					docsPath: './docs',
					stage: 'research_brief',
					model: 'gpt-4o',
					research_context: true,
					council_debate: true,
					idea: ideaText,
					project_name: generatedName
				})
			})
			
			const result = await response.json()
			if (result.success) {
				setCurrentStep('complete')
			}
		} catch (error) {
			console.error('Failed to start journey:', error)
		} finally {
			setIsProcessing(false)
		}
	}

	const renderIdeaInput = () => (
		<div className="border-2 border-blue-200 dark:border-blue-700 rounded-lg p-6 bg-blue-50 dark:bg-blue-900/20">
			<div className="text-center space-y-4">
				<div className="flex justify-center">
					<LightbulbIcon className="w-12 h-12 text-blue-600" />
				</div>
				<h2 className="text-xl font-semibold text-blue-900 dark:text-blue-100">Describe Your Idea</h2>
				<p className="text-sm opacity-80 max-w-lg mx-auto">
					The LLM Council will automatically research your market, analyze competitors, define the problem, 
					identify the industry, and create a complete vision using YC-style best practices.
				</p>
				<div className="space-y-4 max-w-lg mx-auto">
					<div>
						<label className="block text-sm font-medium mb-2 text-left">Describe Your Idea</label>
						<textarea
							value={ideaText}
							onChange={(e) => setIdeaText(e.target.value)}
							placeholder="e.g., A mobile app that helps people track their daily water intake with personalized reminders and integrates with fitness trackers..."
							className="w-full border rounded-lg p-3 h-32 bg-white dark:bg-gray-800 text-sm"
							maxLength={1000}
						/>
						<div className="text-xs opacity-60 text-right mt-1">{ideaText.length}/1000</div>
					</div>
					
					<div className="bg-white dark:bg-gray-800 border rounded-lg p-4 text-left">
						<h3 className="font-medium text-sm mb-2">🚀 What happens next:</h3>
						<ul className="text-xs space-y-1 opacity-80">
							<li>• Research similar products and market opportunities</li>
							<li>• Analyze industry standards and competitive landscape</li>
							<li>• Define problem-solution fit using YC frameworks</li>
							<li>• Create comprehensive vision with success metrics</li>
							<li>• Generate PRD with R-PRD-### requirement IDs</li>
							<li>• Design architecture and implementation plan</li>
						</ul>
					</div>
					
					<div className="flex justify-center">
						<button
							onClick={startFullJourney}
							disabled={!ideaText.trim() || isProcessing}
							className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
						>
							{isProcessing ? (
								<>Processing... <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /></>
							) : (
								<>Start AI Research & Planning <RocketIcon className="w-4 h-4" /></>
							)}
						</button>
					</div>
				</div>
			</div>
		</div>
	)

	const renderProcessing = () => (
		<div className="space-y-6">
			<div className="border rounded-lg p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
				<div className="text-center space-y-4">
					<div className="flex justify-center">
						<SearchIcon className="w-12 h-12 text-blue-600 animate-pulse" />
					</div>
					<h2 className="text-xl font-semibold">Council is Working on "{projectName || generateProjectName(ideaText)}"</h2>
					<p className="text-sm opacity-80 max-w-lg mx-auto">
						Our AI council is researching your idea, analyzing the market, and preparing comprehensive documents...
					</p>
				</div>
			</div>

			{/* Council Members Activity */}
			<div className="border rounded-lg p-4">
				<h3 className="font-semibold mb-4">Council Activity</h3>
				<div className="space-y-3">
					{[
						{ role: 'Research Agent', llm: 'Tavily + GPT-4', activity: 'Gathering market intelligence and competitor analysis', status: 'active' },
						{ role: 'PM Auditor', llm: 'GPT-4o', activity: 'Defining problem-solution fit and YC frameworks', status: 'active' },
						{ role: 'Data Auditor', llm: 'Gemini Pro', activity: 'Identifying success metrics and evaluation frameworks', status: 'pending' },
						{ role: 'Security Auditor', llm: 'Claude 3.5', activity: 'Assessing security requirements and compliance', status: 'pending' },
						{ role: 'Infrastructure Auditor', llm: 'Grok-2', activity: 'Planning technical architecture and scalability', status: 'pending' },
						{ role: 'Cost Auditor', llm: 'GPT-4o', activity: 'Estimating development costs and resource needs', status: 'pending' }
					].map((member, index) => (
						<div key={member.role} className="flex items-center gap-3 p-3 border rounded">
							<div className={`w-3 h-3 rounded-full ${member.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
							<div className="flex-1">
								<div className="font-medium text-sm">{member.role}</div>
								<div className="text-xs opacity-50 mb-1">{member.llm}</div>
								<div className="text-xs opacity-70">{member.activity}</div>
							</div>
							<div className={`text-xs px-2 py-1 rounded ${member.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
								{member.status === 'active' ? 'Working' : 'Queued'}
							</div>
						</div>
					))}
				</div>
			</div>
		</div>
	)

	const renderComplete = () => (
		<div className="space-y-6">
			<div className="border-2 border-green-200 dark:border-green-700 rounded-lg p-6 bg-green-50 dark:bg-green-900/20">
				<div className="text-center space-y-4">
					<div className="flex justify-center">
						<FileTextIcon className="w-12 h-12 text-green-600" />
					</div>
					<h2 className="text-xl font-semibold text-green-900 dark:text-green-100">Research Complete!</h2>
					<p className="text-sm opacity-80 max-w-lg mx-auto">
						The council has created your Research Brief with market analysis, competitor insights, 
						and industry context. Ready for the next phase?
					</p>
					<div className="flex justify-center gap-3">
						<button className="border border-green-600 text-green-700 hover:bg-green-100 px-4 py-2 rounded transition-colors">
							Review Documents
						</button>
						<button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded font-medium transition-colors">
							Continue to Vision
						</button>
					</div>
				</div>
			</div>
		</div>
	)

	return (
		<div className="space-y-6 max-w-4xl mx-auto">
			<div className="text-center">
				<h1 className="text-3xl font-bold">LLM Council</h1>
				<p className="text-sm opacity-70 mt-2">From idea to implementation with AI guidance</p>
			</div>

			{currentStep === 'idea' && renderIdeaInput()}
			{currentStep === 'processing' && renderProcessing()}
			{currentStep === 'complete' && renderComplete()}

			{/* Progress Indicator */}
			<div className="flex justify-center">
				<div className="flex items-center gap-3">
					<div className="flex items-center">
						<div className={`w-3 h-3 rounded-full ${currentStep === 'idea' ? 'bg-blue-600' : currentStep !== 'idea' ? 'bg-green-500' : 'bg-gray-300'}`} />
						<span className="ml-2 text-xs">Idea</span>
					</div>
					<ArrowRightIcon className="w-3 h-3 opacity-50" />
					<div className="flex items-center">
						<div className={`w-3 h-3 rounded-full ${currentStep === 'processing' ? 'bg-blue-600 animate-pulse' : currentStep === 'complete' ? 'bg-green-500' : 'bg-gray-300'}`} />
						<span className="ml-2 text-xs">Research</span>
					</div>
					<ArrowRightIcon className="w-3 h-3 opacity-50" />
					<div className="flex items-center">
						<div className={`w-3 h-3 rounded-full ${currentStep === 'complete' ? 'bg-blue-600' : 'bg-gray-300'}`} />
						<span className="ml-2 text-xs">Documents</span>
					</div>
				</div>
			</div>

			{/* Connection Status */}
			{connectionStatus !== 'connected' && (
				<div className="text-center text-xs opacity-60 text-red-600">
					⚠️ Backend connection: {connectionStatus}
				</div>
			)}
		</div>
	)
}
