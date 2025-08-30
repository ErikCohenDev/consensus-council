import { LightbulbIcon, RocketIcon } from 'lucide-react'
import { useId, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useConnectionState } from '@/stores/appStore'

export const IdeaPage = () => {
	const { connectionStatus } = useConnectionState()
	const navigate = useNavigate()
	const ideaInputId = useId()
	const [ideaText, setIdeaText] = useState('')
	const [isProcessing, setIsProcessing] = useState(false)

	const generateProjectName = (idea: string) => {
		const words = idea.split(' ').slice(0, 3)
		return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
	}

	const startJourney = async () => {
		if (!ideaText.trim()) return

		setIsProcessing(true)
		const projectName = generateProjectName(ideaText)

		try {
			// Step 1: Extract context graph from idea
			const response = await fetch('/api/ideas/extract-context', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					text: ideaText,
					project_name: projectName,
					focus_areas: []
				}),
			})

			const result = await response.json()
			if (result.success) {
				// Store the graph data for context page
				localStorage.setItem('llm-council.current-graph', JSON.stringify(result.data))
				
				// Navigate to context page to visualize and expand
				navigate('/context')
			} else {
				console.error('Context extraction failed:', result.error)
			}
		} catch (error) {
			console.error('Failed to start journey:', error)
		} finally {
			setIsProcessing(false)
		}
	}

	return (
		<div className="h-full flex items-center justify-center">
			<div className="max-w-2xl w-full mx-auto p-8">
				<div className="text-center space-y-6">
					<div className="flex justify-center">
						<LightbulbIcon className="w-16 h-16 text-blue-600" />
					</div>

					<div>
						<h1 className="text-3xl font-bold text-blue-900 dark:text-blue-100 mb-2">
							What's your idea?
						</h1>
						<p className="text-lg opacity-80 max-w-xl mx-auto">
							The LLM Council will research your market, analyze competitors, and create a complete
							vision using industry best practices.
						</p>
					</div>

					<div className="space-y-4">
						<div>
							<label htmlFor={ideaInputId} className="sr-only">
								Describe Your Idea
							</label>
							<textarea
								id={ideaInputId}
								value={ideaText}
								onChange={(e) => setIdeaText(e.target.value)}
								placeholder="e.g., A mobile app that helps people track their daily water intake with personalized reminders and integrates with fitness trackers..."
								className="w-full border-2 border-blue-200 dark:border-blue-700 rounded-lg p-4 h-32 bg-white dark:bg-gray-800 text-lg focus:border-blue-500 focus:outline-none transition-colors resize-none"
								maxLength={1000}
								aria-describedby={`${ideaInputId}-counter`}
							/>
							<div id={`${ideaInputId}-counter`} className="text-sm opacity-60 text-right mt-2">
								{ideaText.length}/1000
							</div>
						</div>

						<button
							type="button"
							onClick={startJourney}
							disabled={!ideaText.trim() || isProcessing}
							className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors flex items-center justify-center gap-3"
						>
							{isProcessing ? (
								<>
									Starting Research...
									<div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
								</>
							) : (
								<>
									Generate Context Graph
									<RocketIcon className="w-5 h-5" />
								</>
							)}
						</button>
					</div>
				</div>

				{connectionStatus !== 'connected' && (
					<div className="text-center text-sm opacity-60 text-red-600 mt-6">
						⚠️ Backend connection: {connectionStatus}
					</div>
				)}
			</div>
		</div>
	)
}
