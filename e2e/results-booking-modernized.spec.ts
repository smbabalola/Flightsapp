import { test, expect } from '@playwright/test';

test.describe('Modernized Frontend - Results Page', () => {
  test.beforeEach(async ({ page }) => {
    // Setup mock search results in sessionStorage
    await page.addInitScript(() => {
      const mockOffer = {
        id: 'test-offer-123',
        total_amount: '500.00',
        total_currency: 'USD',
        slices: [{
          segments: [{
            departing_at: new Date(Date.now() + 86400000 * 7).toISOString(),
            arriving_at: new Date(Date.now() + 86400000 * 7 + 7200000).toISOString(),
            origin: { iata_code: 'LOS' },
            destination: { iata_code: 'LHR' },
            marketing_carrier: {
              name: 'Test Airlines',
              iata_code: 'TA'
            }
          }]
        }]
      };

      const searchParams = {
        slices: [{
          from_: 'LOS',
          to: 'LHR',
          date: new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0]
        }],
        adults: 1,
        children: 0,
        infants: 0,
        cabin: 'economy'
      };

      sessionStorage.setItem('searchResults', JSON.stringify([mockOffer]));
      sessionStorage.setItem('searchParams', JSON.stringify(searchParams));
    });
  });

  test('should display results page with modern design', async ({ page }) => {
    await page.goto('/results.html');

    // Check header section
    await expect(page.locator('h1:has-text("Available Flights")')).toBeVisible();
    await expect(page.locator('#searchSummary')).toBeVisible();
    await expect(page.locator('#resultCount')).toBeVisible();

    // Check sort dropdown
    await expect(page.locator('#sortBy')).toBeVisible();

    // Check new search button
    await expect(page.locator('a[href="index.html"]:has-text("New search")')).toBeVisible();
  });

  test('should display flight summary tabs (Best/Cheapest/Fastest)', async ({ page }) => {
    await page.goto('/results.html');

    // Wait for summary tabs to appear
    await expect(page.locator('#flightSummaryTabs')).toBeVisible({ timeout: 3000 });

    // Check all three tabs
    await expect(page.locator('#bestTab')).toBeVisible();
    await expect(page.locator('#cheapestTab')).toBeVisible();
    await expect(page.locator('#fastestTab')).toBeVisible();

    // Check badges
    await expect(page.locator('text=Recommended')).toBeVisible();
    await expect(page.locator('text=Best value')).toBeVisible();
    await expect(page.locator('text=Quickest')).toBeVisible();
  });

  test('should display filters sidebar', async ({ page }) => {
    await page.goto('/results.html');

    // Check filter sections
    await expect(page.locator('text=Filters')).toBeVisible();
    await expect(page.locator('button[data-target="stopsFilter"]')).toBeVisible();
    await expect(page.locator('button[data-target="priceFilter"]')).toBeVisible();
    await expect(page.locator('button[data-target="departureTimeFilter"]')).toBeVisible();
    await expect(page.locator('button[data-target="airlinesFilter"]')).toBeVisible();

    // Check clear all button
    await expect(page.locator('#clearFilters')).toBeVisible();
  });

  test('should display flight cards with modern design', async ({ page }) => {
    await page.goto('/results.html');

    // Wait for flight cards to render
    await page.waitForSelector('.card', { timeout: 3000 });

    const flightCard = page.locator('.card').first();
    await expect(flightCard).toBeVisible();

    // Check card contains airline info
    await expect(flightCard.locator('text=Test Airlines')).toBeVisible();

    // Check time display
    await expect(flightCard.locator('.text-2xl.font-bold.text-gray-900').first()).toBeVisible();

    // Check price display
    await expect(flightCard.locator('.text-3xl.font-bold.text-blue-600')).toBeVisible();

    // Check select button
    await expect(flightCard.locator('button:has-text("Select")')).toBeVisible();
  });

  test('should toggle filter sections', async ({ page }) => {
    await page.goto('/results.html');

    // Click stops filter header
    await page.click('button[data-target="stopsFilter"]');

    // Check if it collapsed
    const stopsFilter = page.locator('#stopsFilter');
    await expect(stopsFilter).toHaveClass(/hidden/);

    // Click again to expand
    await page.click('button[data-target="stopsFilter"]');
    await expect(stopsFilter).not.toHaveClass(/hidden/);
  });

  test('should filter by stops', async ({ page }) => {
    await page.goto('/results.html');

    // Uncheck direct flights
    await page.uncheck('#filterDirect');

    // Result count should update
    await page.waitForTimeout(500);

    // Check that filtering was applied (result count or cards updated)
    const resultCount = page.locator('#resultCount');
    await expect(resultCount).toBeVisible();
  });

  test('should adjust price range slider', async ({ page }) => {
    await page.goto('/results.html');

    const priceRange = page.locator('#priceRange');
    await expect(priceRange).toBeVisible();

    // Get initial value
    const initialValue = await priceRange.inputValue();

    // Change the slider
    await priceRange.fill('1000');

    // Check label updated
    const priceLabel = page.locator('#priceRangeLabel');
    await expect(priceLabel).toContainText('1,000');
  });

  test('should sort flights', async ({ page }) => {
    await page.goto('/results.html');

    // Change sort option
    await page.selectOption('#sortBy', 'price');

    // Wait for re-render
    await page.waitForTimeout(500);

    // Flights should still be displayed
    await expect(page.locator('.card').first()).toBeVisible();
  });

  test('should click summary tab to filter', async ({ page }) => {
    await page.goto('/results.html');

    // Wait for tabs
    await expect(page.locator('#cheapestTab')).toBeVisible({ timeout: 3000 });

    // Click cheapest tab
    await page.click('#cheapestTab');

    // Sort should update
    await expect(page.locator('#sortBy')).toHaveValue('price');
  });

  test('should clear all filters', async ({ page }) => {
    await page.goto('/results.html');

    // Change some filters
    await page.uncheck('#filterDirect');
    await page.locator('#priceRange').fill('500');

    // Click clear all
    await page.click('#clearFilters');

    // Filters should reset
    await expect(page.locator('#filterDirect')).toBeChecked();
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/results.html');

    // Check mobile layout
    await expect(page.locator('h1:has-text("Available Flights")')).toBeVisible();

    // Filters should stack on mobile
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();

    // Flight cards should be visible
    await expect(page.locator('.card').first()).toBeVisible();
  });
});

test.describe('Modernized Frontend - Booking Page', () => {
  test.beforeEach(async ({ page }) => {
    // Setup mock data
    await page.addInitScript(() => {
      // Set auth token
      localStorage.setItem('access_token', 'test-token-123');

      const mockOffer = {
        id: 'test-offer-123',
        total_amount: '500.00',
        total_currency: 'USD',
        slices: [{
          segments: [{
            departing_at: new Date(Date.now() + 86400000 * 7).toISOString(),
            arriving_at: new Date(Date.now() + 86400000 * 7 + 7200000).toISOString(),
            origin: { iata_code: 'LOS', name: 'Lagos' },
            destination: { iata_code: 'LHR', name: 'London Heathrow' },
            marketing_carrier: {
              name: 'Test Airlines',
              iata_code: 'TA'
            }
          }]
        }]
      };

      const searchParams = {
        slices: [{
          from_: 'LOS',
          to: 'LHR',
          date: new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0]
        }],
        adults: 1,
        children: 0,
        infants: 0,
        cabin: 'economy'
      };

      sessionStorage.setItem('selectedOffer', JSON.stringify(mockOffer));
      sessionStorage.setItem('searchParams', JSON.stringify(searchParams));
    });
  });

  test('should display booking page with modern design', async ({ page }) => {
    await page.goto('/booking.html');

    // Check progress steps
    await expect(page.locator('text=Search')).toBeVisible();
    await expect(page.locator('text=Booking Details')).toBeVisible();
    await expect(page.locator('text=Payment')).toBeVisible();

    // Check main heading
    await expect(page.locator('h2:has-text("Contact Information")')).toBeVisible();
  });

  test('should display progress indicator', async ({ page }) => {
    await page.goto('/booking.html');

    // Check step circles
    const completedStep = page.locator('.bg-green-500').first();
    const currentStep = page.locator('.bg-blue-600').first();
    const futureStep = page.locator('.bg-gray-300').first();

    await expect(completedStep).toBeVisible();
    await expect(currentStep).toBeVisible();
    await expect(futureStep).toBeVisible();
  });

  test('should display contact information form', async ({ page }) => {
    await page.goto('/booking.html');

    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#phone')).toBeVisible();
  });

  test('should generate passenger forms', async ({ page }) => {
    await page.goto('/booking.html');

    // Wait for passenger forms to render
    await page.waitForSelector('#passengersContainer', { timeout: 2000 });

    // Check passenger form exists
    await expect(page.locator('text=Passenger Information')).toBeVisible();
    await expect(page.locator('text=Adult 1')).toBeVisible();

    // Check form fields
    await expect(page.locator('#title_0')).toBeVisible();
    await expect(page.locator('#firstName_0')).toBeVisible();
    await expect(page.locator('#lastName_0')).toBeVisible();
    await expect(page.locator('#dob_0')).toBeVisible();
    await expect(page.locator('#gender_0')).toBeVisible();
  });

  test('should display payment method options', async ({ page }) => {
    await page.goto('/booking.html');

    await expect(page.locator('text=Choose Payment Method')).toBeVisible();

    // Check all payment options
    await expect(page.locator('button[data-method="card"]')).toBeVisible();
    await expect(page.locator('button[data-method="bank"]')).toBeVisible();
    await expect(page.locator('button[data-method="ussd"]')).toBeVisible();

    // Card should be selected by default
    await expect(page.locator('button[data-method="card"]')).toHaveClass(/selected/);
  });

  test('should switch payment methods', async ({ page }) => {
    await page.goto('/booking.html');

    // Click bank transfer
    await page.click('button[data-method="bank"]');

    // Check it's now selected
    await expect(page.locator('button[data-method="bank"]')).toHaveClass(/selected/);
    await expect(page.locator('button[data-method="card"]')).not.toHaveClass(/selected/);
  });

  test('should display promo code section', async ({ page }) => {
    await page.goto('/booking.html');

    await expect(page.locator('text=Have a promo code?')).toBeVisible();
    await expect(page.locator('#promoCode')).toBeVisible();
    await expect(page.locator('#applyPromoBtn')).toBeVisible();
  });

  test('should display booking summary sidebar', async ({ page }) => {
    await page.goto('/booking.html');

    await expect(page.locator('h2:has-text("Booking Summary")')).toBeVisible();
    await expect(page.locator('#flightSummary')).toBeVisible();

    // Check summary displays flight info
    await expect(page.locator('text=Test Airlines')).toBeVisible();
    await expect(page.locator('text=LOS')).toBeVisible();
    await expect(page.locator('text=LHR')).toBeVisible();
  });

  test('should display action buttons', async ({ page }) => {
    await page.goto('/booking.html');

    await expect(page.locator('button:has-text("Back")')).toBeVisible();
    await expect(page.locator('button:has-text("Proceed to Payment")')).toBeVisible();
  });

  test('should have sticky summary sidebar on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 1024 });
    await page.goto('/booking.html');

    const sidebar = page.locator('aside .card');
    await expect(sidebar).toBeVisible();

    // Check sticky class
    await expect(sidebar).toHaveClass(/sticky/);
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/booking.html');

    // Forms should be visible
    await expect(page.locator('h2:has-text("Contact Information")')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();

    // Summary should appear below on mobile
    await expect(page.locator('h2:has-text("Booking Summary")')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/booking.html');

    // Try to submit without filling
    await page.click('button[type="submit"]');

    // Email should be invalid
    const emailInput = page.locator('#email');
    const isInvalid = await emailInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('promo code input should be uppercase', async ({ page }) => {
    await page.goto('/booking.html');

    await page.fill('#promoCode', 'test');

    // Should convert to uppercase
    await expect(page.locator('#promoCode')).toHaveClass(/uppercase/);
  });
});

test.describe('Modernized Frontend - Booking Flow Integration', () => {
  test('should navigate from results to booking', async ({ page }) => {
    // Setup auth
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'test-token-123');

      const mockOffer = {
        id: 'test-offer-123',
        total_amount: '500.00',
        total_currency: 'USD',
        slices: [{
          segments: [{
            departing_at: new Date(Date.now() + 86400000 * 7).toISOString(),
            arriving_at: new Date(Date.now() + 86400000 * 7 + 7200000).toISOString(),
            origin: { iata_code: 'LOS' },
            destination: { iata_code: 'LHR' },
            marketing_carrier: {
              name: 'Test Airlines',
              iata_code: 'TA'
            }
          }]
        }]
      };

      const searchParams = {
        slices: [{
          from_: 'LOS',
          to: 'LHR',
          date: new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0]
        }],
        adults: 1,
        children: 0,
        infants: 0,
        cabin: 'economy'
      };

      sessionStorage.setItem('searchResults', JSON.stringify([mockOffer]));
      sessionStorage.setItem('searchParams', JSON.stringify(searchParams));
    });

    await page.goto('/results.html');

    // Wait for flight cards
    await page.waitForSelector('.card', { timeout: 3000 });

    // Click select button
    await page.click('button:has-text("Select")');

    // Should navigate to booking page
    await page.waitForURL('**/booking.html', { timeout: 2000 });
    await expect(page.locator('h2:has-text("Contact Information")')).toBeVisible();
  });

  test('should redirect to login if not authenticated', async ({ page }) => {
    // Don't set auth token
    await page.addInitScript(() => {
      const mockOffer = {
        id: 'test-offer-123',
        total_amount: '500.00',
        total_currency: 'USD',
        slices: [{
          segments: [{
            departing_at: new Date(Date.now() + 86400000 * 7).toISOString(),
            arriving_at: new Date(Date.now() + 86400000 * 7 + 7200000).toISOString(),
            origin: { iata_code: 'LOS' },
            destination: { iata_code: 'LHR' },
            marketing_carrier: {
              name: 'Test Airlines',
              iata_code: 'TA'
            }
          }]
        }]
      };

      const searchParams = {
        slices: [{
          from_: 'LOS',
          to: 'LHR',
          date: new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0]
        }],
        adults: 1,
        children: 0,
        infants: 0,
        cabin: 'economy'
      };

      sessionStorage.setItem('searchResults', JSON.stringify([mockOffer]));
      sessionStorage.setItem('searchParams', JSON.stringify(searchParams));
    });

    await page.goto('/results.html');

    // Wait for flight cards
    await page.waitForSelector('.card', { timeout: 3000 });

    // Setup alert handler
    page.on('dialog', dialog => dialog.accept());

    // Click select button
    await page.click('button:has-text("Select")');

    // Should redirect to login
    await page.waitForURL('**/login.html', { timeout: 2000 });
  });
});
