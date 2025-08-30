import { useAppActions, useAppStore, useUIState } from '@/stores/appStore'

export const SettingsPage = () => {
	const { theme } = useUIState()
	const { setTheme, updateConfiguration } = useAppActions()
	const configuration = useAppStore((s) => s.configuration)

	return (
		<div className="space-y-4">
			<h1 className="text-xl font-semibold">Settings</h1>
			<div className="border rounded p-3 space-y-2">
				<div className="font-medium">Theme</div>
				<select
					value={theme}
					onChange={(e) => setTheme(e.target.value as any)}
					className="border rounded px-2 py-1 bg-transparent"
				>
					<option value="auto">Auto</option>
					<option value="light">Light</option>
					<option value="dark">Dark</option>
				</select>
			</div>

			<div className="border rounded p-3 space-y-2">
				<div className="font-medium">Project</div>
				<label className="block text-sm opacity-80">Project ID</label>
				<input
					className="border rounded px-2 py-1 w-full bg-transparent"
					value={configuration.projectId || ''}
					onChange={(e) => updateConfiguration({ projectId: e.target.value })}
					placeholder="local"
				/>
				<label className="block text-sm opacity-80 mt-2">Docs Path</label>
				<input
					className="border rounded px-2 py-1 w-full bg-transparent"
					value={configuration.docsPath || ''}
					onChange={(e) => updateConfiguration({ docsPath: e.target.value })}
					placeholder="./docs"
				/>
				<p className="text-xs opacity-70">WebSocket connections will scope to the Project ID.</p>
			</div>
		</div>
	)
}
