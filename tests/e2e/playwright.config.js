/**
 * Playwright E2E Test Configuration
 * 
 * VERIFIES: Complete user workflows through Web UI
 * VALIDATES: Cross-browser compatibility and user experience
 * COVERAGE: Chrome, Firefox, Safari on desktop + mobile viewports
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Global test timeout
  timeout: 120000, // 2 minutes for complex workflows
  
  // Expect timeout for assertions
  expect: {
    timeout: 10000
  },
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests for user workflow scenarios (they may conflict)
  workers: process.env.CI ? 1 : 1,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'tests/e2e/reports' }],
    ['json', { outputFile: 'tests/e2e/results.json' }],
    ['list']
  ],
  
  // Global test setup
  use: {
    // Base URL for all tests
    baseURL: 'http://localhost:3000',
    
    // Browser context options
    viewport: { width: 1920, height: 1080 },
    
    // Collect trace on failure for debugging
    trace: 'on-first-retry',
    
    // Capture screenshot on failure
    screenshot: 'only-on-failure',
    
    // Record video on first retry
    video: 'retain-on-failure',
    
    // Ignore HTTPS errors for local development
    ignoreHTTPSErrors: true,
    
    // Default navigation timeout
    navigationTimeout: 30000,
    
    // Default action timeout  
    actionTimeout: 10000
  },

  // Test projects for different browsers and contexts
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.js/,
      teardown: 'cleanup'
    },
    
    // Desktop browsers
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup']
    },
    
    {
      name: 'firefox-desktop',
      use: { ...devices['Desktop Firefox'] },
      dependencies: ['setup']
    },
    
    {
      name: 'webkit-desktop',
      use: { ...devices['Desktop Safari'] },
      dependencies: ['setup']
    },
    
    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      dependencies: ['setup']
    },
    
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
      dependencies: ['setup']
    },
    
    // Cleanup
    {
      name: 'cleanup',
      testMatch: /.*\.cleanup\.js/
    }
  ],

  // Development server configuration
  webServer: [
    {
      command: 'cd frontend && npm run dev',
      port: 3000,
      timeout: 60000,
      reuseExistingServer: !process.env.CI
    },
    {
      command: 'python audit.py ui --debug',
      port: 8000,
      timeout: 30000,
      reuseExistingServer: !process.env.CI
    }
  ],

  // Global setup and teardown
  globalSetup: require.resolve('./global-setup.js'),
  globalTeardown: require.resolve('./global-teardown.js'),

  // Test output directories
  outputDir: 'tests/e2e/test-results',
  
  // Test fixtures and utilities
  testIdAttribute: 'data-testid'
});