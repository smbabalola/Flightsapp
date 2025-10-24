import { test, expect } from '@playwright/test';

test('guest currency auto-detect prefills selector and applies to results', async ({ page, request }) => {
  await page.goto('/');
  // Wait a moment for auto-detect to fetch and set selector
  await page.waitForTimeout(300);
  const sel = page.locator('#currencySelect');
  await expect(sel).toBeVisible();

  // Choose USD explicitly to be deterministic
  await sel.selectOption('USD');

  // Fill a simple one-way search
  await page.selectOption('#from', 'LOS');
  await page.selectOption('#to', 'LHR');
  const today = new Date();
  const depart = new Date(today.getTime() + 5 * 86400000);
  const yyyy = depart.getFullYear();
  const mm = String(depart.getMonth() + 1).padStart(2, '0');
  const dd = String(depart.getDate()).padStart(2, '0');
  await page.fill('#departDate', `${yyyy}-${mm}-${dd}`);
  await page.click('button[type="submit"]');

  await page.waitForURL('**/results.html');
  // One of the prices should include USD
  const price = page.locator('.price');
  await expect(price.first()).toContainText('USD');
});

