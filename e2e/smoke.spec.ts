import { test, expect } from '@playwright/test';

test('health endpoint is up', async ({ request }) => {
  const res = await request.get('/health');
  expect(res.ok()).toBeTruthy();
  const json = await res.json();
  expect(json).toHaveProperty('status');
});

test('homepage serves static content', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/http/);
  // Basic smoke: page has some content
  const content = await page.content();
  expect(content.length).toBeGreaterThan(100);
});

test('search → results → select triggers login when unauthenticated', async ({ page }) => {
  await page.goto('/');
  // Fill search form quickly
  await page.selectOption('#from', 'LOS');
  await page.selectOption('#to', 'LHR');
  const today = new Date();
  const depart = new Date(today.getTime() + 3 * 86400000); // +3 days
  const yyyy = depart.getFullYear();
  const mm = String(depart.getMonth() + 1).padStart(2, '0');
  const dd = String(depart.getDate()).padStart(2, '0');
  await page.fill('#departDate', `${yyyy}-${mm}-${dd}`);
  await page.click('button[type="submit"]');

  // Wait for results page
  await page.waitForURL('**/results.html');
  await expect(page.locator('.results-container')).toBeVisible();

  // Click first "Select Flight"
  const selectButtons = page.locator('button:has-text("Select Flight")');
  await expect(selectButtons.first()).toBeVisible();
  await selectButtons.first().click();

  // Should redirect to login as user is not authenticated
  await page.waitForURL('**/login.html**');
  await expect(page.locator('text=Login')).toBeVisible();
});
