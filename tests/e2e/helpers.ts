import { Page, expect } from '@playwright/test';

// Helper functions for E2E tests

/**
 * Login to the application
 */
export async function login(page: Page, email: string, password: string) {
  await page.goto('/login.html');
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');

  // Wait for login to complete (redirects to dashboard)
  await page.waitForURL('**/dashboard.html', { timeout: 10000 });
}

/**
 * Register a new user
 */
export async function register(page: Page, email: string, password: string, name: string) {
  await page.goto('/signup.html');
  await page.fill('#fullName', name);
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.fill('#confirmPassword', password);
  await page.click('button[type="submit"]');

  // Wait for registration to complete
  await page.waitForURL('**/dashboard.html', { timeout: 10000 });
}

/**
 * Search for flights
 */
export async function searchFlights(
  page: Page,
  from: string,
  to: string,
  departureDate: string,
  returnDate?: string
) {
  await page.goto('/');

  // Fill origin
  await page.fill('#origin', from);
  await page.waitForTimeout(500);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  // Fill destination
  await page.fill('#destination', to);
  await page.waitForTimeout(500);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  // Select departure date
  await page.fill('#departure-date', departureDate);

  // Select return date if provided (round trip)
  if (returnDate) {
    await page.fill('#return-date', returnDate);
  }

  // Add passengers (default 1 adult)
  // Submit search
  await page.click('button[type="submit"], button:has-text("Search")');

  // Wait for results page
  await page.waitForURL('**/results.html*', { timeout: 30000 });

  // Wait for flights to load
  await page.waitForSelector('.flight-card, .offer-card', { timeout: 30000 });
}

/**
 * Select a flight from results
 */
export async function selectFlight(page: Page, flightIndex: number = 0) {
  // Wait for flight cards to be visible
  const flightCards = page.locator('.flight-card, .offer-card');
  await flightCards.first().waitFor({ state: 'visible', timeout: 10000 });

  // Click on the flight card or select button
  const selectButton = flightCards.nth(flightIndex).locator('button:has-text("Select"), button:has-text("Book")');
  await selectButton.click();

  // Wait for navigation to checkout/booking page
  await page.waitForTimeout(1000);
}

/**
 * Fill passenger details
 */
export async function fillPassengerDetails(
  page: Page,
  passenger: {
    title: string;
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    dateOfBirth: string;
  }
) {
  // Wait for passenger form
  await page.waitForSelector('input[name*="first"], input[id*="first"]', { timeout: 5000 });

  // Fill title (if dropdown exists)
  const titleSelect = page.locator('select[name*="title"], select[id*="title"]');
  if (await titleSelect.count() > 0) {
    await titleSelect.selectOption(passenger.title);
  }

  // Fill first name
  await page.fill('input[name*="first"], input[id*="first"]', passenger.firstName);

  // Fill last name
  await page.fill('input[name*="last"], input[id*="last"]', passenger.lastName);

  // Fill email
  const emailInput = page.locator('input[type="email"]');
  if (await emailInput.count() > 0) {
    await emailInput.first().fill(passenger.email);
  }

  // Fill phone
  const phoneInput = page.locator('input[type="tel"], input[name*="phone"]');
  if (await phoneInput.count() > 0) {
    await phoneInput.first().fill(passenger.phone);
  }

  // Fill date of birth
  const dobInput = page.locator('input[name*="birth"], input[id*="dob"]');
  if (await dobInput.count() > 0) {
    await dobInput.first().fill(passenger.dateOfBirth);
  }
}

/**
 * Complete payment (for test environment)
 */
export async function completePayment(page: Page, cardDetails?: any) {
  // Wait for payment section
  await page.waitForSelector('button:has-text("Pay"), button:has-text("Complete"), button:has-text("Confirm")', { timeout: 5000 });

  // If test card details provided, fill them
  if (cardDetails) {
    const cardNumberInput = page.locator('input[name*="card"], iframe[name*="card"]');
    if (await cardNumberInput.count() > 0) {
      // Handle Paystack iframe if present
      // For test mode, we'll just click confirm
    }
  }

  // Click confirm/pay button
  await page.click('button:has-text("Pay"), button:has-text("Complete"), button:has-text("Confirm")');
}

/**
 * Wait for booking confirmation
 */
export async function waitForConfirmation(page: Page) {
  // Wait for confirmation message or page
  await page.waitForSelector(
    'text=/booking confirmed|confirmation|success|thank you/i',
    { timeout: 60000 }
  );

  // Verify booking reference exists
  const bookingRef = page.locator('text=/booking reference|confirmation code|PNR/i');
  await expect(bookingRef).toBeVisible();
}

/**
 * Generate unique email for test user
 */
export function generateTestEmail(): string {
  const timestamp = Date.now();
  return `test.user+${timestamp}@sureflights.test`;
}

/**
 * Get test user credentials
 */
export function getTestCredentials() {
  return {
    email: process.env.TEST_USER_EMAIL || 'admin@sureflights.ng',
    password: process.env.TEST_USER_PASSWORD || 'admin123',
  };
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true
  });
}
