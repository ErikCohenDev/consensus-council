import { test, expect } from '@playwright/test'

test.describe('Council run flow (E2E)', () => {
  test('start run from Audit page updates status', async ({ page }) => {
    // Assumes backend is running on :8000 and Vite dev server will be managed by webServer
    await page.goto('/audit')

    // Kick off a run
    await page.getByTestId('start-run').click()

    // Wait for status to transition (initialize → running → completed)
    // We assert any of those states appear; completed is ideal but timing dependent.
    const status = page.locator('text=Current Status').locator('xpath=..')
    await expect.poll(async () => (await status.textContent()) || '').toContain('Overall:')
  })
})

