import { defineConfig, devices } from '@playwright/test'
import path from 'node:path'

export default defineConfig({
  testDir: 'e2e',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  timeout: 60_000,
  retries: 1,
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // Optionally spin up the Vite dev server for tests.
  // Backend server should be started separately (8000) or via another process manager.
  webServer: {
    command: 'npm run dev',
    port: 3000,
    cwd: path.dirname(new URL(import.meta.url).pathname),
  },
})

