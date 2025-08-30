import { EyeIcon, EyeOffIcon } from 'lucide-react'
import { useId, useState } from 'react'
import { useAppActions, useAppStore, useUIState } from '@/stores/appStore'

export const SettingsPage = () => {
	const { theme } = useUIState()
	const { setTheme, updateConfiguration, updateApiKey, clearApiKey } = useAppActions()
	const configuration = useAppStore((s) => s.configuration)
	const apiKeys = useAppStore((s) => s.apiKeys)

	const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})

	const projectIdInputId = useId()
	const docsPathInputId = useId()

	const toggleShowApiKey = (provider: string) => {
		setShowApiKeys((prev) => ({ ...prev, [provider]: !prev[provider] }))
	}

	return (
		<div className="space-y-4">
			<h1 className="text-xl font-semibold">Settings</h1>
			<div className="border rounded p-3 space-y-2">
				<div className="font-medium">Theme</div>
				<select
					value={theme}
					onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'auto')}
					className="border rounded px-2 py-1 bg-transparent"
				>
					<option value="auto">Auto</option>
					<option value="light">Light</option>
					<option value="dark">Dark</option>
				</select>
			</div>
			<div className="border rounded p-3 space-y-2">
				<div className="font-medium">Project</div>
				<label htmlFor={projectIdInputId} className="block text-sm opacity-80">
					Project ID
				</label>
				<input
					id={projectIdInputId}
					className="border rounded px-2 py-1 w-full bg-transparent"
					value={configuration.projectId || ''}
					onChange={(e) => updateConfiguration({ projectId: e.target.value })}
					placeholder="local"
				/>
				<label htmlFor={docsPathInputId} className="block text-sm opacity-80 mt-2">
					Docs Path
				</label>
				<input
					id={docsPathInputId}
					className="border rounded px-2 py-1 w-full bg-transparent"
					value={configuration.docsPath || ''}
					onChange={(e) => updateConfiguration({ docsPath: e.target.value })}
					placeholder="./docs"
				/>
				<p className="text-xs opacity-70">WebSocket connections will scope to the Project ID.</p>
			</div>

			<div className="border rounded p-3 space-y-4">
				<div className="font-medium">API Keys</div>
				<p className="text-xs opacity-70">
					Configure API keys for LLM providers. Keys are stored locally in your browser.
				</p>

				{[
					{ provider: 'openai', label: 'OpenAI API Key', placeholder: 'sk-...' },
					{ provider: 'anthropic', label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
					{ provider: 'google', label: 'Google API Key', placeholder: 'AIza...' },
					{ provider: 'tavily', label: 'Tavily API Key (Research)', placeholder: 'tvly-...' },
				].map(({ provider, label, placeholder }) => {
					const inputId = `${provider}-api-key`
					return (
						<div key={provider} className="space-y-2">
							<label htmlFor={inputId} className="block text-sm opacity-80">
								{label}
							</label>
							<div className="flex gap-2">
								<div className="relative flex-1">
									<input
										id={inputId}
										type={showApiKeys[provider] ? 'text' : 'password'}
										className="border rounded px-2 py-1 w-full bg-transparent pr-10"
										value={apiKeys[provider] || ''}
										onChange={(e) => updateApiKey(provider, e.target.value)}
										placeholder={placeholder}
									/>
									<button
										type="button"
										onClick={() => toggleShowApiKey(provider)}
										className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-50 hover:opacity-100"
									>
										{showApiKeys[provider] ? (
											<EyeOffIcon className="w-4 h-4" />
										) : (
											<EyeIcon className="w-4 h-4" />
										)}
									</button>
								</div>
								{apiKeys[provider] && (
									<button
										type="button"
										onClick={() => clearApiKey(provider)}
										className="px-3 py-1 text-sm border rounded opacity-70 hover:opacity-100"
									>
										Clear
									</button>
								)}
							</div>
						</div>
					)
				})}

				<div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border-l-4 border-blue-400">
					<div className="text-sm font-medium text-blue-800 dark:text-blue-200">Security Note</div>
					<div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
						API keys are stored locally in your browser and never sent to our servers. You can also
						set environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
					</div>
				</div>
			</div>
		</div>
	)
}
