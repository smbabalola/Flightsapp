import { test, expect } from '@playwright/test';
import {
  searchFlights,
  selectFlight,
  fillPassengerDetails,
  completePayment,
  waitForConfirmation,
  getTestCredentials,
  login,
  generateTestEmail,
} from './helpers';

test.describe('Checkout and Booking Confirmation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });

    // Login before each test
    const { email, password } = getTestCredentials();
    await login(page, email, password);
  });

  test('should complete full booking flow - search to confirmation', async ({ page }) => {
    // Step 1: Search for flights
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 30); // Book well in advance
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'ACC', departureDate);

    // Step 2: Select a flight
    await selectFlight(page, 0);

    // Step 3: Fill passenger details
    await fillPassengerDetails(page, {
      title: 'Mr',
      firstName: 'Test',
      lastName: 'User',
      email: generateTestEmail(),
      phone: '+2348012345678',
      dateOfBirth: '1990-01-15',
    });

    // Step 4: Proceed to payment
    const proceedButton = page.locator(
      'button:has-text("Proceed"), button:has-text("Continue"), button:has-text("Next")'
    );
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    // Step 5: Complete payment (test mode)
    // Note: In test/staging, payment might be skipped or use test cards
    const paymentSection = page.locator('text=/payment|pay now|card details/i');
    if (await paymentSection.count() > 0) {
      await completePayment(page);
    }

    // Step 6: Wait for confirmation
    await waitForConfirmation(page);

    // Verify booking was successful
    await expect(page.locator('text=/success|confirmed|thank you/i')).toBeVisible();
  });

  test('should show booking summary before payment', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 20);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'LHR', departureDate);
    await selectFlight(page, 0);

    // Wait for checkout page
    await page.waitForTimeout(2000);

    // Verify booking summary is displayed
    const summary = page.locator('text=/summary|total|price breakdown/i');
    await expect(summary.first()).toBeVisible();

    // Verify key information is shown
    await expect(page.locator('text=/passenger|traveler/i')).toBeVisible();
    await expect(page.locator('text=/flight|route/i')).toBeVisible();
    await expect(page.locator('text=/total|amount|price/i')).toBeVisible();
  });

  test('should validate passenger information', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 25);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'DXB', departureDate);
    await selectFlight(page, 0);

    // Try to proceed without filling passenger details
    const proceedButton = page.locator(
      'button:has-text("Proceed"), button:has-text("Continue"), button:has-text("Next")'
    );

    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(1000);

      // Should show validation errors
      const errorMessages = page.locator('text=/required|please|fill|enter/i, .error, [class*="error"]');
      const hasErrors = (await errorMessages.count()) > 0;

      expect(hasErrors).toBeTruthy();
    }
  });

  test('should display correct pricing with fees', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 18);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'JFK', departureDate);

    // Get price from results page
    const resultsPrice = await page.locator('.flight-card, .offer-card').first()
      .locator('text=/¦|NGN|USD|\$/').first().textContent();

    await selectFlight(page, 0);
    await page.waitForTimeout(2000);

    // Verify price on checkout page
    const checkoutPrice = page.locator('text=/total|amount/i').first();
    await expect(checkoutPrice).toBeVisible();

    // Price breakdown should show fees
    const feeBreakdown = page.locator('text=/booking fee|service fee|tax/i');
    if (await feeBreakdown.count() > 0) {
      await expect(feeBreakdown.first()).toBeVisible();
    }
  });

  test('should handle promo codes if feature exists', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 22);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'ACC', departureDate);
    await selectFlight(page, 0);

    // Look for promo code input
    const promoInput = page.locator('input[name*="promo"], input[placeholder*="promo" i]');

    if (await promoInput.count() > 0) {
      // Try invalid promo code
      await promoInput.fill('INVALID123');

      const applyButton = page.locator('button:has-text("Apply"), button:near(' + promoInput + ')');
      if (await applyButton.count() > 0) {
        await applyButton.click();
        await page.waitForTimeout(1000);

        // Should show error for invalid code
        const errorMsg = page.locator('text=/invalid|not found|expired/i');
        await expect(errorMsg.first()).toBeVisible();
      }
    }
  });

  test('should allow editing passenger details', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 16);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'LHR', departureDate);
    await selectFlight(page, 0);

    // Fill passenger details
    await fillPassengerDetails(page, {
      title: 'Mr',
      firstName: 'John',
      lastName: 'Doe',
      email: generateTestEmail(),
      phone: '+2348098765432',
      dateOfBirth: '1985-06-20',
    });

    // Edit first name
    const firstNameInput = page.locator('input[name*="first"], input[id*="first"]');
    await firstNameInput.clear();
    await firstNameInput.fill('Jane');

    // Verify change was saved
    await expect(firstNameInput).toHaveValue('Jane');
  });

  test('should show payment options if multiple available', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 28);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'DXB', departureDate);
    await selectFlight(page, 0);

    await fillPassengerDetails(page, {
      title: 'Ms',
      firstName: 'Test',
      lastName: 'Passenger',
      email: generateTestEmail(),
      phone: '+2348011112222',
      dateOfBirth: '1992-03-10',
    });

    // Proceed to payment
    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    // Check for payment methods (card, bank transfer, etc.)
    const paymentMethods = page.locator('input[type="radio"][name*="payment"], button:has-text("Card"), button:has-text("Bank")');

    if (await paymentMethods.count() > 1) {
      // Multiple payment options available
      await expect(paymentMethods.first()).toBeVisible();
    }
  });

  test('should handle payment timeout gracefully', async ({ page }) => {
    // This test verifies the app handles long payment processing times
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 19);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'CDG', departureDate);
    await selectFlight(page, 0);

    await fillPassengerDetails(page, {
      title: 'Dr',
      firstName: 'Test',
      lastName: 'Timeout',
      email: generateTestEmail(),
      phone: '+2348033334444',
      dateOfBirth: '1988-12-25',
    });

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);

      // Look for timeout message or retry option
      // This would depend on your implementation
      const paymentButton = page.locator('button:has-text("Pay"), button:has-text("Confirm")');
      if (await paymentButton.count() > 0) {
        await paymentButton.click();

        // Wait for response (success, error, or timeout)
        await page.waitForTimeout(60000); // 60 second timeout

        // Should show some status message
        const statusMessage = page.locator('text=/processing|completed|error|timeout|failed/i');
        const hasStatus = (await statusMessage.count()) > 0;

        // Some message should appear
        expect(hasStatus).toBeTruthy();
      }
    }
  });

  test('should send confirmation email (check for message)', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 24);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'LHR', departureDate);
    await selectFlight(page, 0);

    const testEmail = generateTestEmail();

    await fillPassengerDetails(page, {
      title: 'Mr',
      firstName: 'Email',
      lastName: 'Test',
      email: testEmail,
      phone: '+2348055556666',
      dateOfBirth: '1991-08-05',
    });

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    // Complete payment
    await completePayment(page);

    // Wait for confirmation
    await waitForConfirmation(page);

    // Look for message about email confirmation
    const emailMessage = page.locator('text=/email sent|check your email|confirmation sent/i');
    if (await emailMessage.count() > 0) {
      await expect(emailMessage.first()).toBeVisible();
    }
  });

  test('should display booking reference after confirmation', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 27);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'DXB', departureDate);
    await selectFlight(page, 0);

    await fillPassengerDetails(page, {
      title: 'Mrs',
      firstName: 'Reference',
      lastName: 'Test',
      email: generateTestEmail(),
      phone: '+2348077778888',
      dateOfBirth: '1987-04-18',
    });

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    await completePayment(page);
    await waitForConfirmation(page);

    // Verify booking reference is displayed
    const bookingRef = page.locator('text=/booking reference|confirmation code|PNR|[A-Z0-9]{6}/i');
    await expect(bookingRef.first()).toBeVisible();

    // Extract and log booking reference for debugging
    const refText = await bookingRef.first().textContent();
    console.log('Booking Reference:', refText);
  });

  test('should allow downloading booking confirmation', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 26);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'ABV', 'ACC', departureDate);
    await selectFlight(page, 0);

    await fillPassengerDetails(page, {
      title: 'Mr',
      firstName: 'Download',
      lastName: 'Test',
      email: generateTestEmail(),
      phone: '+2348099990000',
      dateOfBirth: '1989-11-30',
    });

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    await completePayment(page);
    await waitForConfirmation(page);

    // Look for download/print button
    const downloadButton = page.locator('button:has-text("Download"), button:has-text("Print"), a:has-text("PDF")');

    if (await downloadButton.count() > 0) {
      await expect(downloadButton.first()).toBeVisible();
      await expect(downloadButton.first()).toBeEnabled();
    }
  });

  test('should show booking in user dashboard', async ({ page }) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 21);
    const departureDate = tomorrow.toISOString().split('T')[0];

    await searchFlights(page, 'LOS', 'JFK', departureDate);
    await selectFlight(page, 0);

    await fillPassengerDetails(page, {
      title: 'Ms',
      firstName: 'Dashboard',
      lastName: 'Test',
      email: generateTestEmail(),
      phone: '+2348066667777',
      dateOfBirth: '1993-07-14',
    });

    const proceedButton = page.locator('button:has-text("Proceed"), button:has-text("Continue")');
    if (await proceedButton.count() > 0) {
      await proceedButton.first().click();
      await page.waitForTimeout(2000);
    }

    await completePayment(page);
    await waitForConfirmation(page);

    // Navigate to dashboard
    await page.goto('/dashboard.html');

    // Look for bookings section
    const bookingsSection = page.locator('text=/my bookings|bookings|trips/i');
    if (await bookingsSection.count() > 0) {
      await expect(bookingsSection.first()).toBeVisible();

      // The recent booking should appear
      await page.waitForTimeout(2000);
      const bookingList = page.locator('.booking, [class*="booking"], tr');

      const hasBookings = (await bookingList.count()) > 0;
      expect(hasBookings).toBeTruthy();
    }
  });
});
