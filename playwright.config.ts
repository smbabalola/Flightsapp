import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 90_000,  // Increased for full booking flow
  retries: 2,  // More retries for staging environment
  reporter: [
    ['html', { open: 'never' }],
    ['allure-playwright']
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:8001',
    headless: process.env.HEADLESS === 'false' ? false : true,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
