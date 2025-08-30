import React from 'react'
import ReactDOM from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'

import App from './App.tsx'
import './index.css'
import './otel'

// Configure React Query
const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			retry: 2,
			staleTime: 5 * 60 * 1000, // 5 minutes
			cacheTime: 10 * 60 * 1000, // 10 minutes
			refetchOnWindowFocus: false,
		},
		mutations: {
			retry: 1,
		},
	},
})

ReactDOM.createRoot(document.getElementById('root')!).render(
	<React.StrictMode>
		<BrowserRouter>
			<QueryClientProvider client={queryClient}>
				<App />
				<Toaster
					position="top-right"
					toastOptions={{
						duration: 4000,
						className: 'text-sm',
						success: {
							iconTheme: {
								primary: '#10b981',
								secondary: '#ffffff',
							},
						},
						error: {
							iconTheme: {
								primary: '#ef4444',
								secondary: '#ffffff',
							},
						},
					}}
				/>
			</QueryClientProvider>
		</BrowserRouter>
	</React.StrictMode>
)
