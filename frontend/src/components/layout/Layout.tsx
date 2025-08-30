import type { PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'
import { useAppActions, useConnectionState, useUIState } from '@/stores/appStore'

const StatusDot = ({
	status,
}: {
	status: 'connecting' | 'connected' | 'disconnected' | 'error'
}) => {
	const color =
		status === 'connected'
			? 'bg-green-500'
			: status === 'connecting'
				? 'bg-yellow-500'
				: status === 'error'
					? 'bg-red-500'
					: 'bg-gray-400'
	return <span className={`inline-block w-2.5 h-2.5 rounded-full mr-2 ${color}`} />
}

export const Layout = ({ children }: PropsWithChildren) => {
	const { connectionStatus } = useConnectionState()
	const { theme } = useUIState()
	const { setTheme } = useAppActions()

	return (
		<div className="min-h-screen flex">
			<aside className="w-56 border-r border-gray-200 dark:border-gray-800 p-4">
				<div className="font-semibold mb-4">LLM Council</div>
				<nav className="flex flex-col gap-2">
					<NavLink to="/" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Idea
					</NavLink>
					<NavLink to="/context" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Context
					</NavLink>
					<NavLink to="/documents" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Documents
					</NavLink>
					<NavLink to="/council" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Council
					</NavLink>
					<NavLink to="/pipeline" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Pipeline
					</NavLink>
					<NavLink to="/settings" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
						Settings
					</NavLink>
				</nav>
			</aside>

			<main className="flex-1 flex flex-col">
				<header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
					<div className="flex items-center text-sm">
						<StatusDot status={connectionStatus} />
						<span className="opacity-70 capitalize">{connectionStatus}</span>
					</div>
					<div className="flex items-center gap-2 text-sm">
						<span>Theme:</span>
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
				</header>
				<div className="flex-1 overflow-hidden">{children}</div>
			</main>
		</div>
	)
}
