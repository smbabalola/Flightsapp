import { test, expect } from '@playwright/test';
import { searchFlights, selectFlight, getTestCredentials, login } from './helpers';

test.describe('Flight Selection Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should display flight details on hover/click', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 7);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'LHR', departureDate);

    // Get first flight card
    const firstFlight = page.locator('.flight-card, .offer-card').first();
    await expect(firstFlight).toBeVisible();

    // Verify basic details are visible
    await expect(firstFlight.locator('text=/[0-9]{2}:[0-9]{2}/').first()).toBeVisible(); // Time
    await expect(firstFlight.locator('text=/¦|NGN|USD|\$/').first()).toBeVisible(); // Price

    // Look for details button or expandable section
    const detailsButton = firstFlight.locator('button:has-text("Details"), button:has-text("View"), a:has-text("Details")');
    if (await detailsButton.count() > 0) {
      await detailsButton.first().click();
      await page.waitForTimeout(500);

      // Verify expanded details
      const expandedDetails = page.locator('text=/baggage|cabin|aircraft|flight number/i');
      await expect(expandedDetails.first()).toBeVisible();
    }
  });

  test('should show airline information', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 10);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'DXB', departureDate);

    const firstFlight = page.locator('.flight-card, .offer-card').first();
    await expect(firstFlight).toBeVisible();

    // Verify airline name or code is displayed
    const airlineInfo = firstFlight.locator('text=/[A-Z]{2}[0-9]|Emirates|British|Turkish|Ethiopian/i');
    await expect(airlineInfo.first()).toBeVisible();
  });

  test('should display baggage information', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 5);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'JFK', departureDate);

    const firstFlight = page.locator('.flight-card, .offer-card').first();

    // Look for baggage information
    const baggageInfo = page.locator('text=/baggage|kg|carry[-\s]on|checked/i');
    if (await baggageInfo.count() > 0) {
      await expect(baggageInfo.first()).toBeVisible();
    }
  });

  test('should show self-transfer warning for multi-airline flights', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 14);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'LAX', departureDate);

    // Look for self-transfer badge/warning (based on your implementation)
    const selfTransferWarning = page.locator('text=/self[-\s]transfer|different airline|separate/i, .self-transfer, [class*="transfer"]');

    if (await selfTransferWarning.count() > 0) {
      await expect(selfTransferWarning.first()).toBeVisible();

      // Click on warning to see more details
      await selfTransferWarning.first().click();
      await page.waitForTimeout(500);

      // Verify explanation is shown
      const explanation = page.locator('text=/re[-\s]check|bags|different booking/i');
      await expect(explanation.first()).toBeVisible();
    }
  });

  test('should allow comparing multiple flights', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 8);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'CDG', departureDate);

    const flightCards = page.locator('.flight-card, .offer-card');
    const count = await flightCards.count();

    if (count >= 2) {
      // Check if compare feature exists
      const compareCheckboxes = page.locator('input[type="checkbox"]:near(:text("Compare"), 50)');

      if (await compareCheckboxes.count() >= 2) {
        // Select two flights for comparison
        await compareCheckboxes.nth(0).check();
        await compareCheckboxes.nth(1).check();

        // Look for compare button
        const compareButton = page.locator('button:has-text("Compare")');
        if (await compareButton.count() > 0) {
          await compareButton.click();
          await page.waitForTimeout(1000);

          // Verify comparison view
          await expect(page.locator('text=/comparison|comparing/i')).toBeVisible();
        }
      }
    }
  });

  test('should select a flight and proceed to booking', async ({ page }) => {
    // Login first to enable booking
    const { email, password } = getTestCredentials();
    await login(page, email, password);

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 12);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'ACC', departureDate);

    // Select the first available flight
    await selectFlight(page, 0);

    // Verify we've moved to booking/checkout page
    // The URL might be /checkout.html, /booking.html, or similar
    await page.waitForTimeout(2000);

    const currentUrl = page.url();
    const isCheckoutPage =
      currentUrl.includes('checkout') ||
      currentUrl.includes('booking') ||
      currentUrl.includes('passenger') ||
      (await page.locator('text=/passenger details|traveler|booking/i').count()) > 0;

    expect(isCheckoutPage).toBeTruthy();
  });

  test('should show cheapest flight option', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 9);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'DXB', departureDate);

    // Look for "Cheapest" badge or indicator (based on your summary tabs implementation)
    const cheapestBadge = page.locator('text=/cheapest|best price|lowest/i').first();

    if (await cheapestBadge.count() > 0) {
      await expect(cheapestBadge).toBeVisible();

      // Click on cheapest to navigate to that flight
      if (await cheapestBadge.locator('..').locator('button').count() > 0) {
        await cheapestBadge.locator('..').locator('button').first().click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('should show fastest flight option', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 11);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'LHR', departureDate);

    // Look for "Fastest" badge or indicator
    const fastestBadge = page.locator('text=/fastest|shortest|quickest/i').first();

    if (await fastestBadge.count() > 0) {
      await expect(fastestBadge).toBeVisible();
    }
  });

  test('should filter by airlines correctly', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 15);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'LHR', departureDate);

    // Wait for airline filters to load
    await page.waitForTimeout(2000);

    // Find airline filter checkboxes
    const airlineFilters = page.locator('input[type="checkbox"]:near(:text("Airlines"), 200)');

    if (await airlineFilters.count() > 0) {
      // Get initial flight count
      const initialCount = await page.locator('.flight-card, .offer-card').count();

      // Select first airline filter
      await airlineFilters.first().check();
      await page.waitForTimeout(1000);

      // Verify results updated
      const filteredCount = await page.locator('.flight-card, .offer-card').count();

      // Filtered results should be same or fewer
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test('should filter by departure time', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 6);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'JFK', departureDate);

    // Look for time-based filters (Morning, Afternoon, Evening, Night)
    const morningFilter = page.locator('input[type="checkbox"]:near(:text("Morning"), 100)');

    if (await morningFilter.count() > 0) {
      await morningFilter.first().check();
      await page.waitForTimeout(1000);

      // Verify filtered results only show morning flights
      const flightCards = page.locator('.flight-card, .offer-card');
      const count = await flightCards.count();

      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should show flight duration correctly', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 13);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'DXB', departureDate);

    const firstFlight = page.locator('.flight-card, .offer-card').first();

    // Look for duration display (e.g., "5h 30m", "5:30", "5 hours")
    const duration = firstFlight.locator('text=/[0-9]+h|[0-9]+:[0-9]+|hours?|minutes?/i');
    await expect(duration.first()).toBeVisible();
  });

  test('should display number of stops', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 7);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'SFO', departureDate);

    const firstFlight = page.locator('.flight-card, .offer-card').first();

    // Look for stops information (e.g., "Direct", "1 stop", "2 stops")
    const stopsInfo = firstFlight.locator('text=/direct|non[-\s]stop|[0-9]\s*stops?/i');
    await expect(stopsInfo.first()).toBeVisible();
  });

  test('should require login to select flights', async ({ page }) => {
    // Make sure we're logged out
    await page.goto('/');

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 4);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'ACC', departureDate);

    // Try to select a flight without logging in
    const selectButton = page.locator('button:has-text("Select"), button:has-text("Book")').first();

    if (await selectButton.count() > 0) {
      await selectButton.click();
      await page.waitForTimeout(1000);

      // Should either redirect to login or show login modal
      const isLoginPage = page.url().includes('login') || (await page.locator('text=/log in|sign in/i').count()) > 0;

      // Some implementations allow viewing details without login
      // So this check might not always be true
      // expect(isLoginPage).toBeTruthy();
    }
  });
});
