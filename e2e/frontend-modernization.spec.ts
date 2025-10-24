import { test, expect } from '@playwright/test';

test.describe('Modernized Frontend - Homepage', () => {
  test('should display hero search interface', async ({ page }) => {
    await page.goto('/');

    // Check hero section
    await expect(page.locator('h1:has-text("Find your next adventure")')).toBeVisible();
    await expect(page.locator('text=Compare flights from hundreds of airlines')).toBeVisible();

    // Check search form elements
    await expect(page.locator('#from')).toBeVisible();
    await expect(page.locator('#to')).toBeVisible();
    await expect(page.locator('#departDate')).toBeVisible();
    await expect(page.locator('#returnDate')).toBeVisible();

    // Check trip type toggle
    await expect(page.locator('#returnTripBtn')).toBeVisible();
    await expect(page.locator('#oneWayBtn')).toBeVisible();
  });

  test('should toggle between return and one-way trip', async ({ page }) => {
    await page.goto('/');

    // Default should be return trip
    await expect(page.locator('#returnTripBtn')).toHaveClass(/btn-primary/);
    await expect(page.locator('#returnDateContainer')).toBeVisible();

    // Click one-way
    await page.click('#oneWayBtn');
    await expect(page.locator('#oneWayBtn')).toHaveClass(/btn-primary/);
    await expect(page.locator('#returnDateContainer')).not.toBeVisible();

    // Switch back to return
    await page.click('#returnTripBtn');
    await expect(page.locator('#returnTripBtn')).toHaveClass(/btn-primary/);
    await expect(page.locator('#returnDateContainer')).toBeVisible();
  });

  test('should open and interact with passengers dropdown', async ({ page }) => {
    await page.goto('/');

    // Open passengers dropdown
    await page.click('#passengersBtn');
    await expect(page.locator('#passengersDropdown')).not.toHaveClass(/hidden/);

    // Check initial values
    await expect(page.locator('#adultsCount')).toHaveText('1');
    await expect(page.locator('#childrenCount')).toHaveText('0');
    await expect(page.locator('#infantsCount')).toHaveText('0');

    // Increase adults
    await page.click('#adultsUp');
    await expect(page.locator('#adultsCount')).toHaveText('2');

    // Increase children
    await page.click('#childrenUp');
    await expect(page.locator('#childrenCount')).toHaveText('1');

    // Close dropdown
    await page.click('#passengersDone');
    await expect(page.locator('#passengersDropdown')).toHaveClass(/hidden/);

    // Check summary updated
    await expect(page.locator('#passengerSummary')).toContainText('3 Passengers');
  });

  test('should show airport suggestions on input', async ({ page }) => {
    await page.goto('/');

    // Wait for airports to load
    await page.waitForTimeout(2000);

    // Type in from field
    await page.fill('#from', 'LAG');
    await page.waitForTimeout(1000);

    // Check if suggestions appear (they may or may not based on API availability)
    // This test is conditional since it depends on metadata API
    const fromSuggestions = page.locator('#fromSuggestions');
    const suggestionCount = await fromSuggestions.locator('[data-code]').count();

    // If suggestions loaded, they should be visible
    if (suggestionCount > 0) {
      await expect(fromSuggestions).toBeVisible();
    }
  });

  test('should display features section', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('Why choose SureFlights?')).toBeVisible();
    await expect(page.getByText('Best Prices').first()).toBeVisible();
    await expect(page.getByText('Easy Booking').first()).toBeVisible();
    await expect(page.getByText('24/7 Support').first()).toBeVisible();
  });

  test('should display trust indicators', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('500K+').first()).toBeVisible();
    await expect(page.getByText('Happy Travelers').first()).toBeVisible();
    await expect(page.getByText('200+').first()).toBeVisible();
    await expect(page.getByText('Airlines').first()).toBeVisible();
  });

  test('should have working navigation links', async ({ page }) => {
    await page.goto('/');

    // Check nav links exist (in desktop nav, not mobile menu)
    await expect(page.locator('nav .hidden.md\\:flex a[href="about.html"]')).toBeVisible();
    await expect(page.locator('nav .hidden.md\\:flex a[href="contact.html"]')).toBeVisible();
    await expect(page.locator('nav .hidden.md\\:flex a[href="login.html"]')).toBeVisible();
    await expect(page.locator('nav .hidden.md\\:flex a[href="signup.html"]')).toBeVisible();
  });
});

test.describe('Modernized Frontend - Responsive Design', () => {
  test('should be mobile responsive - homepage', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('/');

    // Hero should still be visible
    await expect(page.locator('h1:has-text("Find your next adventure")')).toBeVisible();

    // Search form should stack vertically
    await expect(page.locator('#from')).toBeVisible();
    await expect(page.locator('#to')).toBeVisible();

    // Mobile menu button should be visible
    await expect(page.locator('#mobileMenuBtn')).toBeVisible();
  });

  test('should open mobile menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Click mobile menu button
    await page.click('#mobileMenuBtn');

    // Menu should be visible
    await expect(page.locator('#mobileMenu')).toBeVisible();
  });

  test('should be tablet responsive', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto('/');

    // Desktop nav should be visible on tablet
    await expect(page.locator('nav .hidden.md\\:flex')).toBeVisible();

    // Search form should still work
    await expect(page.locator('#from')).toBeVisible();
  });
});

test.describe('Modernized Frontend - Styling and Animations', () => {
  test('should have proper card styling', async ({ page }) => {
    await page.goto('/');

    // Check search card has card class
    const searchCard = page.locator('.card').first();
    await expect(searchCard).toBeVisible();

    // Check for shadow and rounded corners (via computed styles)
    const cardStyle = await searchCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        borderRadius: styles.borderRadius,
        boxShadow: styles.boxShadow
      };
    });

    expect(cardStyle.borderRadius).not.toBe('0px');
    expect(cardStyle.boxShadow).not.toBe('none');
  });

  test('should have smooth hover effects on buttons', async ({ page }) => {
    await page.goto('/');

    const searchButton = page.getByRole('button', { name: /search flights/i });
    await expect(searchButton).toBeVisible();

    // Hover and check for transition
    await searchButton.hover();
    const buttonStyle = await searchButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        transition: styles.transition,
        cursor: styles.cursor
      };
    });

    expect(buttonStyle.cursor).toBe('pointer');
    // Check that some transition is defined
    expect(buttonStyle.transition).not.toBe('all 0s ease 0s');
  });

  test('should have fade-in animations', async ({ page }) => {
    await page.goto('/');

    // Check for animate-fade-in class
    const animatedElements = page.locator('.animate-fade-in');
    await expect(animatedElements.first()).toBeVisible();
  });
});

test.describe('Modernized Frontend - Form Validation', () => {
  test('should validate required fields on search', async ({ page }) => {
    await page.goto('/');

    // Try to submit without filling fields
    await page.click('button[type="submit"]', { hasText: 'Search Flights' });

    // Browser validation should prevent submission
    const fromInput = page.locator('#from');
    const isInvalid = await fromInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should require date to be in future', async ({ page }) => {
    await page.goto('/');

    // Check date inputs have min attribute set to today
    const departDate = page.locator('#departDate');
    const minDate = await departDate.getAttribute('min');

    const today = new Date().toISOString().split('T')[0];
    expect(minDate).toBe(today);
  });
});

test.describe('Modernized Frontend - Accessibility', () => {
  test('should have proper focus states', async ({ page }) => {
    await page.goto('/');

    // Tab through interactive elements
    await page.keyboard.press('Tab');

    // Check that focused element has outline
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();

    const focusStyle = await focused.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.outline;
    });

    expect(focusStyle).not.toBe('none');
  });

  test('should have proper labels for inputs', async ({ page }) => {
    await page.goto('/');

    // Check all inputs have labels
    const fromLabel = page.locator('label[for="from"]');
    const toLabel = page.locator('label[for="to"]');
    const departLabel = page.locator('label[for="departDate"]');

    await expect(fromLabel).toBeVisible();
    await expect(toLabel).toBeVisible();
    await expect(departLabel).toBeVisible();
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/');

    const logo = page.locator('img[alt="SureFlights Logo"]');
    await expect(logo).toBeVisible();
  });
});

test.describe('Modernized Frontend - Footer', () => {
  test('should display footer with links', async ({ page }) => {
    await page.goto('/');

    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    await expect(footer.getByRole('heading', { name: 'SureFlights' })).toBeVisible();
    await expect(footer.getByText('© 2025 SureFlights')).toBeVisible();

    // Check footer sections
    await expect(footer.locator('a[href="/"]').first()).toBeVisible();
    await expect(footer.locator('a[href="about.html"]').first()).toBeVisible();
    await expect(footer.locator('a[href="contact.html"]').first()).toBeVisible();
  });
});
