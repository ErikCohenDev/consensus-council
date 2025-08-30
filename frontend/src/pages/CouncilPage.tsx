import { useEffect, useMemo, useState } from 'react'
import { CheckIcon, DollarSignIcon, FileTextIcon, InfoIcon, UsersIcon, XIcon } from 'lucide-react'
import { useAppStore, useCouncilState } from '@/stores/appStore'

type PersonalityType = {
	id: string
	name: string
	description: string
	promptStyle: string
}

type AuditorRole = {
	id: string
	name: string
	description: string
	specialization: string
	defaultModel: string
	suggestedModels: { provider: string; model: string; description: string }[]
	defaultPersonality: string
	basePrompt: string
}

type CouncilConfiguration = {
	selectedAuditors: string[]
	auditorModels: Record<string, string>
	auditorPersonalities: Record<string, string>
}

export const CouncilPage = () => {
	const { activeDebateSession } = useCouncilState()
	const apiKeys = useAppStore((s) => s.apiKeys)
	const [selectedMember, setSelectedMember] = useState<string | null>(null)

	// Cost assumptions per debate meeting
	const [rounds, setRounds] = useState<number>(2)
	const [tokensInPerRound, setTokensInPerRound] = useState<number>(800)
	const [tokensOutPerRound, setTokensOutPerRound] = useState<number>(600)

	const [config, setConfig] = useState<CouncilConfiguration>({
		selectedAuditors: ['research', 'pm', 'data', 'security', 'scope'],
		auditorModels: {
			research: 'gpt-4o',
			pm: 'gpt-4o',
			data: 'gemini-1.5-pro',
			security: 'claude-3-5-sonnet',
			infrastructure: 'grok-2',
			cost: 'gpt-4o',
			scope: 'claude-3-5-sonnet',
		},
		auditorPersonalities: {
			research: 'balanced',
			pm: 'optimist',
			data: 'critic',
			security: 'critic',
			infrastructure: 'balanced',
			cost: 'critic',
			scope: 'critic',
		},
	})

	// Expanded model catalog with indicative pricing per 1K tokens
	const MODEL_CATALOG: Record<
		string,
		{
			provider: string
			label: string
			inPricePer1K: number
			outPricePer1K: number
			contextK?: number
		}
	> = {
		// OpenAI
		'gpt-4o': {
			provider: 'OpenAI',
			label: 'gpt-4o',
			inPricePer1K: 0.005,
			outPricePer1K: 0.015,
			contextK: 128,
		},
		'gpt-4o-mini': {
			provider: 'OpenAI',
			label: 'gpt-4o-mini',
			inPricePer1K: 0.00015,
			outPricePer1K: 0.0006,
			contextK: 128,
		},
		'gpt-4.1': {
			provider: 'OpenAI',
			label: 'gpt-4.1',
			inPricePer1K: 0.005,
			outPricePer1K: 0.015,
			contextK: 128,
		},
		'gpt-4-turbo': {
			provider: 'OpenAI',
			label: 'gpt-4-turbo',
			inPricePer1K: 0.01,
			outPricePer1K: 0.03,
			contextK: 128,
		},
		// Anthropic
		'claude-3-5-sonnet': {
			provider: 'Anthropic',
			label: 'claude-3.5-sonnet',
			inPricePer1K: 0.003,
			outPricePer1K: 0.015,
			contextK: 200,
		},
		'claude-3-opus': {
			provider: 'Anthropic',
			label: 'claude-3-opus',
			inPricePer1K: 0.015,
			outPricePer1K: 0.075,
			contextK: 200,
		},
		'claude-3-5-haiku': {
			provider: 'Anthropic',
			label: 'claude-3.5-haiku',
			inPricePer1K: 0.0008,
			outPricePer1K: 0.004,
			contextK: 200,
		},
		// Google
		'gemini-1.5-pro': {
			provider: 'Google',
			label: 'gemini-1.5-pro',
			inPricePer1K: 0.003,
			outPricePer1K: 0.015,
			contextK: 1000,
		},
		'gemini-1.5-flash': {
			provider: 'Google',
			label: 'gemini-1.5-flash',
			inPricePer1K: 0.00035,
			outPricePer1K: 0.00053,
			contextK: 1000,
		},
		// Meta
		'llama-3.1-70b-instruct': {
			provider: 'Meta',
			label: 'llama-3.1-70b-instruct',
			inPricePer1K: 0.0009,
			outPricePer1K: 0.0009,
			contextK: 128,
		},
		'llama-3.1-8b-instruct': {
			provider: 'Meta',
			label: 'llama-3.1-8b-instruct',
			inPricePer1K: 0.0002,
			outPricePer1K: 0.0002,
			contextK: 128,
		},
		// Mistral
		'mistral-large-2407': {
			provider: 'Mistral',
			label: 'mistral-large-2407',
			inPricePer1K: 0.002,
			outPricePer1K: 0.006,
			contextK: 128,
		},
		// xAI
		'grok-2': {
			provider: 'xAI',
			label: 'grok-2',
			inPricePer1K: 0.002,
			outPricePer1K: 0.006,
			contextK: 128,
		},
		// Cohere
		'command-r-plus': {
			provider: 'Cohere',
			label: 'command-r+',
			inPricePer1K: 0.003,
			outPricePer1K: 0.015,
			contextK: 128,
		},
	}

	const allModelOptions = Object.entries(MODEL_CATALOG)
		.map(([key, v]) => ({ key, provider: v.provider, label: v.label }))
		.sort((a, b) => (a.provider + a.label).localeCompare(b.provider + b.label))

	const hasLLMProviders = useMemo(
		() => Boolean(apiKeys.openai || apiKeys.anthropic || apiKeys.google),
		[apiKeys]
	)

	const hasTavily = Boolean(apiKeys.tavily)

	const personalityTypes: PersonalityType[] = [
		{
			id: 'optimist',
			name: 'Optimist',
			description: 'Focuses on opportunities and positive outcomes',
			promptStyle:
				'Approach with enthusiasm and highlight potential benefits. Look for ways to make things work.',
		},
		{
			id: 'critic',
			name: 'Critic',
			description: 'Identifies risks, challenges, and potential problems',
			promptStyle:
				'Be thorough in finding issues, risks, and gaps. Challenge assumptions and push for better solutions.',
		},
		{
			id: 'balanced',
			name: 'Balanced',
			description: 'Objective analysis weighing pros and cons',
			promptStyle:
				'Provide balanced analysis considering both benefits and drawbacks. Focus on practical solutions.',
		},
		{
			id: 'innovator',
			name: 'Innovator',
			description: 'Pushes for creative and cutting-edge solutions',
			promptStyle:
				'Think outside the box and suggest innovative approaches. Consider emerging technologies and trends.',
		},
	]

	const availableAuditors: AuditorRole[] = [
		{
			id: 'research',
			name: 'Research Agent',
			description: 'Market intelligence and competitor analysis',
			specialization: 'Market Research, Competitive Analysis, Industry Trends',
			defaultModel: 'gpt-4o',
			defaultPersonality: 'balanced',
			basePrompt:
				'You are a market research expert. Analyze the market, identify competitors, and provide data-driven insights about industry trends and opportunities.',
			suggestedModels: [
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Best for comprehensive research' },
				{ provider: 'OpenAI', model: 'gpt-4o-mini', description: 'Faster, cost-effective' },
				{ provider: 'Anthropic', model: 'claude-3-5-sonnet', description: 'Excellent reasoning' },
			],
		},
		{
			id: 'pm',
			name: 'PM Auditor',
			description: 'Product strategy and YC-style frameworks',
			specialization: 'Product Strategy, YC Frameworks, Problem-Solution Fit',
			defaultModel: 'gpt-4o',
			defaultPersonality: 'optimist',
			basePrompt:
				'You are a product manager expert specializing in YC frameworks. Focus on product-market fit, user needs, and strategic business decisions.',
			suggestedModels: [
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Strong strategic thinking' },
				{ provider: 'Anthropic', model: 'claude-3-5-sonnet', description: 'Excellent analysis' },
				{ provider: 'OpenAI', model: 'gpt-4-turbo', description: 'Good balance of speed/quality' },
			],
		},
		{
			id: 'data',
			name: 'Data Auditor',
			description: 'Success metrics and evaluation frameworks',
			specialization: 'Analytics, KPIs, Success Metrics, Evaluation Frameworks',
			defaultModel: 'gemini-pro',
			defaultPersonality: 'critic',
			basePrompt:
				'You are a data analytics expert. Define measurable success metrics, KPIs, and evaluation frameworks to track product performance.',
			suggestedModels: [
				{ provider: 'Google', model: 'gemini-pro', description: 'Strong analytical capabilities' },
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Comprehensive analysis' },
				{ provider: 'Anthropic', model: 'claude-3-5-sonnet', description: 'Detailed reasoning' },
			],
		},
		{
			id: 'security',
			name: 'Security Auditor',
			description: 'Security requirements and compliance',
			specialization: 'Security Architecture, Compliance, Risk Assessment',
			defaultModel: 'claude-3-5-sonnet',
			defaultPersonality: 'critic',
			basePrompt:
				'You are a security expert. Identify security risks, compliance requirements, and design secure architectures. Think like an attacker.',
			suggestedModels: [
				{
					provider: 'Anthropic',
					model: 'claude-3-5-sonnet',
					description: 'Top security reasoning',
				},
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Comprehensive security analysis' },
				{ provider: 'Anthropic', model: 'claude-3-opus', description: 'Deep security expertise' },
			],
		},
		{
			id: 'scope',
			name: 'Scope Creep Auditor',
			description: 'Prevents feature bloat and maintains focus',
			specialization: 'MVP Definition, Feature Prioritization, Scope Management',
			defaultModel: 'claude-3-5-sonnet',
			defaultPersonality: 'critic',
			basePrompt:
				'You are a scope management expert. Your job is to prevent feature creep, challenge unnecessary complexity, and keep the project focused on core value proposition.',
			suggestedModels: [
				{
					provider: 'Anthropic',
					model: 'claude-3-5-sonnet',
					description: 'Excellent at logical reasoning',
				},
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Strong analytical thinking' },
				{ provider: 'OpenAI', model: 'gpt-4o-mini', description: 'Quick scope validation' },
			],
		},
		{
			id: 'infrastructure',
			name: 'Infrastructure Auditor',
			description: 'Technical architecture and scalability',
			specialization: 'System Architecture, Scalability, DevOps, Cloud Strategy',
			defaultModel: 'grok-2',
			defaultPersonality: 'balanced',
			basePrompt:
				'You are a senior infrastructure engineer. Design scalable, maintainable technical architectures and deployment strategies.',
			suggestedModels: [
				{ provider: 'OpenRouter', model: 'grok-2', description: 'Latest technical knowledge' },
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Strong technical design' },
				{
					provider: 'Anthropic',
					model: 'claude-3-5-sonnet',
					description: 'Excellent architecture',
				},
			],
		},
		{
			id: 'cost',
			name: 'Cost Auditor',
			description: 'Resource estimation and budget planning',
			specialization: 'Cost Estimation, Resource Planning, ROI Analysis',
			defaultModel: 'gpt-4o',
			defaultPersonality: 'critic',
			basePrompt:
				'You are a business analyst focused on cost optimization. Estimate development costs, resource needs, and ROI calculations.',
			suggestedModels: [
				{ provider: 'OpenAI', model: 'gpt-4o', description: 'Accurate cost modeling' },
				{ provider: 'OpenAI', model: 'gpt-4o-mini', description: 'Quick estimates' },
				{ provider: 'Anthropic', model: 'claude-3-5-sonnet', description: 'Detailed analysis' },
			],
		},
	]

	const toggleAuditor = (auditorId: string) => {
		if (!hasLLMProviders) return
		if (auditorId === 'research' && !hasTavily) return
		setConfig((prev) => ({
			...prev,
			selectedAuditors: prev.selectedAuditors.includes(auditorId)
				? (() => {
						if (prev.selectedAuditors.length <= 2) {
							// Enforce minimum of 2 council members
							return prev.selectedAuditors
						}
						return prev.selectedAuditors.filter((id) => id !== auditorId)
					})()
				: [...prev.selectedAuditors, auditorId],
		}))
	}

	const updateAuditorModel = (auditorId: string, model: string) => {
		setConfig((prev) => ({
			...prev,
			auditorModels: { ...prev.auditorModels, [auditorId]: model },
		}))
	}

	const updateAuditorPersonality = (auditorId: string, personality: string) => {
		setConfig((prev) => ({
			...prev,
			auditorPersonalities: { ...prev.auditorPersonalities, [auditorId]: personality },
		}))
	}

	const generateFullPrompt = (auditor: AuditorRole, personality: string) => {
		const personalityData = personalityTypes.find((p) => p.id === personality)
		return `${auditor.basePrompt}\n\nPersonality: ${personalityData?.promptStyle || 'Provide balanced analysis.'}\n\nFocus areas: ${auditor.specialization}`
	}

	const selectedAuditorData = selectedMember
		? availableAuditors.find((a) => a.id === selectedMember)
		: null

	useEffect(() => {
		if (!hasTavily && config.selectedAuditors.includes('research')) {
			setConfig((prev) => ({
				...prev,
				selectedAuditors: prev.selectedAuditors.filter((id) => id !== 'research'),
			}))
		}
	}, [hasTavily, config.selectedAuditors])

	const estimateModelCost = (
		modelKey: string,
		inTokens: number,
		outTokens: number,
		numRounds: number
	) => {
		const pricing = MODEL_CATALOG[modelKey]
		if (!pricing) return 0
		const inCost = (inTokens / 1000) * pricing.inPricePer1K
		const outCost = (outTokens / 1000) * pricing.outPricePer1K
		return (inCost + outCost) * Math.max(1, numRounds)
	}

	const totalEstimatedCost = config.selectedAuditors.reduce((sum, auditorId) => {
		const modelKey = config.auditorModels[auditorId]
		if (!modelKey) return sum
		return sum + estimateModelCost(modelKey, tokensInPerRound, tokensOutPerRound, rounds)
	}, 0)

	return (
		<div className="h-full flex">
			{/* Main Council View */}
			<div className="flex-1 flex flex-col">
				{/* Header */}
				<div className="border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-6 py-4">
					<h1 className="text-xl font-semibold flex items-center gap-2">
						<UsersIcon className="w-5 h-5" />
						LLM Council
					</h1>
					<p className="text-sm opacity-70">Configure your AI council members and their models</p>
				</div>

				{/* Council Grid */}
				<div className="flex-1 p-6">
					{/* Cost Estimation */}
					<div className="mb-6 border rounded-lg p-4 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-700">
						<div className="flex items-center justify-between">
							<h3 className="font-semibold mb-1 text-emerald-900 dark:text-emerald-100 flex items-center gap-2">
								<DollarSignIcon className="w-4 h-4" />
								Cost Estimation
							</h3>
							<div className="text-xs text-gray-600 dark:text-gray-300 flex items-center gap-1">
								<InfoIcon className="w-3 h-3" />
								Prices are approximate per 1K tokens
							</div>
						</div>
						<div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-2">
							<div>
								<div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Rounds</div>
								<input
									type="number"
									min={1}
									value={rounds}
									onChange={(e) => setRounds(Number(e.target.value) || 1)}
									className="w-full border rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
								/>
							</div>
							<div>
								<div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
									Input tokens / round
								</div>
								<input
									type="number"
									min={0}
									value={tokensInPerRound}
									onChange={(e) => setTokensInPerRound(Math.max(0, Number(e.target.value) || 0))}
									className="w-full border rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
								/>
							</div>
							<div>
								<div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
									Output tokens / round
								</div>
								<input
									type="number"
									min={0}
									value={tokensOutPerRound}
									onChange={(e) => setTokensOutPerRound(Math.max(0, Number(e.target.value) || 0))}
									className="w-full border rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
								/>
							</div>
							<div className="self-end">
								<div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Estimated total</div>
								<div className="text-lg font-semibold">${totalEstimatedCost.toFixed(2)}</div>
							</div>
						</div>
					</div>

					{/* Selected Council Summary */}
					<div className="mb-6 border rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700">
						<h3 className="font-semibold mb-3 text-blue-900 dark:text-blue-100">
							Selected Council ({config.selectedAuditors.length} members)
						</h3>
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
							{config.selectedAuditors.map((auditorId) => {
								const auditor = availableAuditors.find((a) => a.id === auditorId)
								const model = config.auditorModels[auditorId]
								if (!auditor) return null

								const personality =
									config.auditorPersonalities[auditorId] || auditor.defaultPersonality
								const personalityData = personalityTypes.find((p) => p.id === personality)
								const perMemberCost = model
									? estimateModelCost(model, tokensInPerRound, tokensOutPerRound, rounds)
									: 0

								return (
									<div
										key={auditorId}
										className="border rounded p-3 bg-white dark:bg-blue-800 border-blue-300 dark:border-blue-600"
									>
										<div className="font-medium text-sm">{auditor.name}</div>
										<div className="text-xs text-blue-600 dark:text-blue-400 font-mono mb-1">
											{model}
										</div>
										<div className="flex items-center justify-between">
											<div className="text-xs text-gray-600 dark:text-gray-300">
												{personalityData?.name}
											</div>
											<div className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">
												${perMemberCost.toFixed(2)}
											</div>
										</div>
										<button
											type="button"
											onClick={() => setSelectedMember(auditor.id)}
											className="mt-2 inline-flex items-center gap-1 text-xs text-gray-700 dark:text-gray-200 hover:underline"
										>
											<FileTextIcon className="w-3 h-3" /> View prompt
										</button>
									</div>
								)
							})}
						</div>
					</div>

					<div className="grid grid-cols-2 lg:grid-cols-3 gap-4 h-fit">
						{availableAuditors.map((auditor) => {
							const isSelected = config.selectedAuditors.includes(auditor.id)
							const selectedModel = config.auditorModels[auditor.id] || auditor.defaultModel

							return (
								<button
									key={auditor.id}
									type="button"
									onClick={() => setSelectedMember(auditor.id)}
									className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
										isSelected
											? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
											: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300'
									}`}
								>
									{/* Selection Checkbox */}
									<div className="absolute top-2 right-2">
										<button
											onClick={(e) => {
												e.stopPropagation()
												toggleAuditor(auditor.id)
											}}
											type="button"
											className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
												isSelected
													? 'border-blue-500 bg-blue-500'
													: 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
											}`}
										>
											{isSelected && <CheckIcon className="w-3 h-3 text-white" />}
										</button>
									</div>

									{/* Auditor Info */}
									<div className="pr-8">
										<h3 className="font-semibold text-base mb-2">{auditor.name}</h3>
										<p className="text-sm opacity-70 mb-3">{auditor.description}</p>

										{isSelected && (
											<div className="text-xs">
												<div className="text-gray-600 dark:text-gray-400 mb-1">Model:</div>
												<div className="font-mono text-blue-600 dark:text-blue-400">
													{selectedModel}
												</div>
											</div>
										)}
									</div>

									{/* Active Indicator */}
									{isSelected && (
										<div className="absolute bottom-2 left-2">
											<div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
										</div>
									)}
								</button>
							)
						})}
					</div>

					{/* Active Session Info */}
					{activeDebateSession && (
						<div className="mt-6 border rounded-lg p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700">
							<h3 className="font-semibold mb-2">Active Debate Session</h3>
							<div className="text-sm">
								Stage:{' '}
								<span className="capitalize font-medium">{activeDebateSession.documentStage}</span>
							</div>
							<div className="text-xs opacity-70 mt-1">
								Council members are currently debating and refining the document
							</div>
						</div>
					)}
				</div>
			</div>

			{/* Right Panel - Member Settings */}
			{selectedMember && selectedAuditorData && (
				<div className="w-96 border-l dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
					{/* Panel Header */}
					<div className="border-b dark:border-gray-700 px-4 py-3 flex items-center justify-between">
						<h3 className="font-semibold">{selectedAuditorData.name} Settings</h3>
						<button
							onClick={() => setSelectedMember(null)}
							type="button"
							className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
						>
							<XIcon className="w-4 h-4" />
						</button>
					</div>

					{/* Panel Content */}
					<div className="flex-1 p-4 space-y-6">
						{/* Basic Info */}
						<div>
							<h4 className="font-medium mb-2">Role</h4>
							<p className="text-sm opacity-70 mb-3">{selectedAuditorData.description}</p>
							<div className="text-xs text-gray-600 dark:text-gray-400">
								<strong>Specialization:</strong> {selectedAuditorData.specialization}
							</div>
						</div>

						{/* Personality Selection */}
						<div>
							<h4 className="font-medium mb-2">Personality</h4>
							<select
								value={
									config.auditorPersonalities[selectedAuditorData.id] ||
									selectedAuditorData.defaultPersonality
								}
								onChange={(e) => updateAuditorPersonality(selectedAuditorData.id, e.target.value)}
								className="w-full border rounded px-3 py-2 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
							>
								{personalityTypes.map((p) => (
									<option key={p.id} value={p.id}>
										{p.name}
									</option>
								))}
							</select>
							<p className="text-xs text-gray-500 mt-1">
								{
									personalityTypes.find(
										(p) =>
											p.id ===
											(config.auditorPersonalities[selectedAuditorData.id] ||
												selectedAuditorData.defaultPersonality)
									)?.description
								}
							</p>
						</div>

						{/* Model Selection */}
						<div>
							<h4 className="font-medium mb-2">Foundational Model</h4>
							<select
								value={
									config.auditorModels[selectedAuditorData.id] || selectedAuditorData.defaultModel
								}
								onChange={(e) => updateAuditorModel(selectedAuditorData.id, e.target.value)}
								className="w-full border rounded px-3 py-2 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
							>
								{/* Suggested models first */}
								{selectedAuditorData.suggestedModels.map((modelOption) => (
									<option key={modelOption.model} value={modelOption.model}>
										{modelOption.provider} {modelOption.model}
									</option>
								))}
								<option disabled>──────────</option>
								{/* Full catalog */}
								{allModelOptions.map((opt) => (
									<option key={`all-${opt.key}`} value={opt.key}>
										{opt.provider} {opt.label}
									</option>
								))}
							</select>
							<div className="text-xs text-gray-500 mt-1 space-y-1">
								<div>
									{selectedAuditorData.suggestedModels.find(
										(m) =>
											m.model ===
											(config.auditorModels[selectedAuditorData.id] ||
												selectedAuditorData.defaultModel)
									)?.description || 'Selected from catalog'}
								</div>
								<div className="text-gray-600 dark:text-gray-300">
									{(() => {
										const m =
											MODEL_CATALOG[
												config.auditorModels[selectedAuditorData.id] ||
													selectedAuditorData.defaultModel
											]
										if (!m) return null
										return `~$${m.inPricePer1K.toFixed(4)}/1K in, $${m.outPricePer1K.toFixed(4)}/1K out`
									})()}
								</div>
							</div>
						</div>

						{/* Prompt Preview */}
						<div className="pt-2">
							<h4 className="font-medium mb-2">Prompt Preview</h4>
							<textarea
								readOnly
								className="w-full h-40 border rounded px-3 py-2 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
								value={generateFullPrompt(
									selectedAuditorData,
									config.auditorPersonalities[selectedAuditorData.id] ||
										selectedAuditorData.defaultPersonality
								)}
							/>
						</div>

						{/* Selection Toggle */}
						<div className="pt-4 border-t dark:border-gray-700">
							<button
								onClick={() => toggleAuditor(selectedAuditorData.id)}
								type="button"
								className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
									config.selectedAuditors.includes(selectedAuditorData.id)
										? 'bg-red-100 hover:bg-red-200 text-red-700 dark:bg-red-900/20 dark:text-red-400'
										: 'bg-blue-100 hover:bg-blue-200 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
								}`}
							>
								{config.selectedAuditors.includes(selectedAuditorData.id)
									? 'Remove from Council'
									: 'Add to Council'}
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	)
}
