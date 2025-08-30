import { motion } from 'framer-motion'
import { Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/layout/Layout'
import { useWebSocketConnection } from '@/hooks/useWebSocketConnection'
import { AuditPage } from '@/pages/AuditPage'
import { CouncilPage } from '@/pages/CouncilPage'
import { IdeaPage } from '@/pages/IdeaPage'
import { PipelinePage } from '@/pages/PipelinePage'
import { SettingsPage } from '@/pages/SettingsPage'
import { useAppStore } from '@/stores/appStore'

function App() {
	// Initialize WebSocket connection
	useWebSocketConnection()

	// Get theme from store
	const { theme } = useAppStore()

	return (
		<div
			className={`min-h-screen transition-colors duration-200 ${
				theme === 'dark'
					? 'dark bg-gray-900 text-white'
					: theme === 'light'
						? 'bg-gray-50 text-gray-900'
						: 'bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white'
			}`}
		>
			<Layout>
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.3 }}
					className="h-full"
				>
					<Routes>
						<Route path="/" element={<IdeaPage />} />
						<Route path="/documents" element={<AuditPage />} />
						<Route path="/council" element={<CouncilPage />} />
						<Route path="/pipeline" element={<PipelinePage />} />
						<Route path="/settings" element={<SettingsPage />} />
					</Routes>
				</motion.div>
			</Layout>
		</div>
	)
}

export default App
