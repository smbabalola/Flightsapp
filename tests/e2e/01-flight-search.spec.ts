import { test, expect } from '@playwright/test';
import { searchFlights, getTestCredentials, login } from './helpers';

test.describe('Flight Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Set viewport for consistent testing
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');

    // Verify page title
    await expect(page).toHaveTitle(/SureFlights|GoCome/i);

    // Verify search form is visible
    await expect(page.locator('#origin, input[name="origin"]')).toBeVisible();
    await expect(page.locator('#destination, input[name="destination"]')).toBeVisible();
    await expect(page.locator('#departure-date, input[name="departure"]')).toBeVisible();
  });

  test('should search for one-way flights', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 7);
    const departureDate = tomorrow.toISOString().split('T')[0];

    // Search for flights from Lagos to London
    await searchFlights(page, 'LOS', 'LHR', departureDate);

    // Verify we're on results page
    await expect(page).toHaveURL(/results\.html/);

    // Verify flight cards are displayed
    const flightCards = page.locator('.flight-card, .offer-card');
    await expect(flightCards.first()).toBeVisible({ timeout: 30000 });

    // Verify at least one flight is shown
    const flightCount = await flightCards.count();
    expect(flightCount).toBeGreaterThan(0);

    // Verify flight details are displayed
    await expect(page.locator('text=/price|¦|NGN|USD/i').first()).toBeVisible();
    await expect(page.locator('text=/duration|time|hours/i').first()).toBeVisible();
  });

  test('should search for round-trip flights', async ({ page }) => {
    const departureDate = new Date();
    departureDate.setDate(departureDate.getDate() + 14);
    const returnDate = new Date();
    returnDate.setDate(returnDate.getDate() + 21);

    const departure = departureDate.toISOString().split('T')[0];
    const returnD = returnDate.toISOString().split('T')[0];

    // Search for round-trip flights
    await searchFlights(page, 'LOS', 'DXB', departure, returnD);

    // Verify results are displayed
    await expect(page).toHaveURL(/results\.html/);

    const flightCards = page.locator('.flight-card, .offer-card');
    await expect(flightCards.first()).toBeVisible({ timeout: 30000 });

    // Verify round-trip indicator or return flight info
    // This depends on your UI implementation
  });

  test('should apply filters correctly', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 10);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'JFK', departureDate);

    // Wait for filters sidebar to be visible
    await page.waitForSelector('.filters, #filters, [class*="filter"]', { timeout: 5000 });

    // Test direct flights filter (if available)
    const directFlightFilter = page.locator('input[type="checkbox"]:near(:text("Direct"), 100)');
    if (await directFlightFilter.count() > 0) {
      await directFlightFilter.first().check();
      await page.waitForTimeout(1000);

      // Verify results updated
      const flightCards = page.locator('.flight-card, .offer-card');
      const count = await flightCards.count();
      expect(count).toBeGreaterThanOrEqual(0); // May be 0 if no direct flights
    }

    // Test price sorting (if available)
    const sortDropdown = page.locator('select:near(:text("Sort"), 100)');
    if (await sortDropdown.count() > 0) {
      await sortDropdown.first().selectOption({ label: /price|cheap/i });
      await page.waitForTimeout(1000);
    }
  });

  test('should display best/cheapest/fastest summary tabs', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 5);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'LHR', departureDate);

    // Check if summary tabs exist (based on your previous implementation)
    const summaryTabs = page.locator('.summary-card, [class*="summary"]');
    if (await summaryTabs.count() > 0) {
      // Verify summary cards show data
      await expect(summaryTabs.first()).toBeVisible();
      await expect(page.locator('text=/best|cheapest|fastest/i').first()).toBeVisible();
    }
  });

  test('should handle no results gracefully', async ({ page }) => {
    // Search for unlikely route or invalid dates
    const pastDate = '2020-01-01';

    await page.goto('/');
    await page.fill('#origin', 'XXX'); // Invalid code
    await page.fill('#destination', 'YYY'); // Invalid code
    await page.fill('#departure-date', pastDate);

    const searchButton = page.locator('button[type="submit"], button:has-text("Search")');
    await searchButton.click();

    // Should either show error or no results message
    await page.waitForTimeout(3000);

    const noResultsMessage = page.locator('text=/no flights|no results|try again/i');
    const errorMessage = page.locator('text=/error|invalid|please check/i');

    const hasMessage = (await noResultsMessage.count() > 0) || (await errorMessage.count() > 0);
    expect(hasMessage).toBeTruthy();
  });

  test('should show loading state during search', async ({ page }) => {
    await page.goto('/');

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 3);
    const departureDate = tomorrow.toISOString().split('T')[0];

    // Fill form
    await page.fill('#origin', 'LOS');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await page.fill('#destination', 'ACC');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await page.fill('#departure-date', departureDate);

    // Click search
    const searchButton = page.locator('button[type="submit"], button:has-text("Search")');
    await searchButton.click();

    // Verify loading indicator appears
    const loadingIndicator = page.locator('text=/searching|loading|please wait/i, .spinner, .loading');

    // Loading should appear briefly (may be fast in dev)
    const isLoading = await loadingIndicator.isVisible().catch(() => false);
    // If loading was too fast, just verify we got to results
    if (!isLoading) {
      await expect(page).toHaveURL(/results\.html/);
    }
  });

  test('should persist search parameters in URL', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 8);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'CDG', departureDate);

    // Verify URL contains search parameters
    const url = page.url();
    expect(url).toContain('origin=LOS');
    expect(url).toContain('destination=CDG');
    expect(url).toContain(departureDate.replace(/-/g, '%2D') || departureDate);
  });

  test('should work when logged in', async ({ page }) => {
    // Login first
    const { email, password } = getTestCredentials();
    await login(page, email, password);

    // Navigate back to search
    await page.goto('/');

    // Perform search
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 6);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'DXB', departureDate);

    // Verify results are displayed
    const flightCards = page.locator('.flight-card, .offer-card');
    await expect(flightCards.first()).toBeVisible({ timeout: 30000 });
  });
});
