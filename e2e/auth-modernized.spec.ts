import { test, expect } from '@playwright/test';

test.describe('Modernized Frontend - Login Page', () => {
  test('should display login form with modern design', async ({ page }) => {
    await page.goto('/login.html');

    // Check title and subtitle
    await expect(page.locator('h1:has-text("Welcome back")')).toBeVisible();
    await expect(page.locator('text=Log in to your SureFlights account')).toBeVisible();

    // Check form elements
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#remember')).toBeVisible();

    // Check links
    await expect(page.locator('a[href="forgot-password.html"]')).toBeVisible();
    await expect(page.locator('a[href="signup.html"]')).toHaveCount(2); // Nav + footer link

    // Check submit button
    await expect(page.locator('button[type="submit"]:has-text("Log In")')).toBeVisible();
  });

  test('should have centered card layout', async ({ page }) => {
    await page.goto('/login.html');

    const card = page.locator('.card');
    await expect(card).toBeVisible();

    // Check card styling
    const cardStyle = await card.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        borderRadius: styles.borderRadius,
        boxShadow: styles.boxShadow,
        backgroundColor: styles.backgroundColor
      };
    });

    expect(cardStyle.borderRadius).not.toBe('0px');
    expect(cardStyle.boxShadow).not.toBe('none');
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/login.html');

    // Fill invalid email
    await page.fill('#email', 'invalid-email');
    await page.fill('#password', 'password123');

    // Try to submit
    await page.click('button[type="submit"]');

    // Browser validation should catch it
    const emailInput = page.locator('#email');
    const isInvalid = await emailInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should require all fields', async ({ page }) => {
    await page.goto('/login.html');

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Email should be invalid
    const emailInput = page.locator('#email');
    const isInvalid = await emailInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should redirect to dashboard if already logged in', async ({ page }) => {
    // Set a token in localStorage
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'fake-token-for-redirect-test');
    });

    await page.goto('/login.html');

    // Should redirect to dashboard
    await page.waitForURL('**/dashboard.html', { timeout: 2000 });
  });

  test('should have gradient background', async ({ page }) => {
    await page.goto('/login.html');

    const body = page.locator('body');
    const bodyStyle = await body.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundImage: styles.backgroundImage
      };
    });

    expect(bodyStyle.backgroundImage).toContain('gradient');
  });
});

test.describe('Modernized Frontend - Signup Page', () => {
  test('should display signup form with modern design', async ({ page }) => {
    await page.goto('/signup.html');

    // Check title and subtitle
    await expect(page.locator('h1:has-text("Create your account")')).toBeVisible();
    await expect(page.locator('text=Start booking flights with SureFlights')).toBeVisible();

    // Check form elements
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#confirmPassword')).toBeVisible();
    await expect(page.locator('#terms')).toBeVisible();

    // Check submit button
    await expect(page.locator('button[type="submit"]:has-text("Create Account")')).toBeVisible();
  });

  test('should display benefits section', async ({ page }) => {
    await page.goto('/signup.html');

    // Check benefits
    await expect(page.locator('text=Best Prices Guaranteed')).toBeVisible();
    await expect(page.locator('text=Secure Booking')).toBeVisible();
    await expect(page.locator('text=24/7 Support')).toBeVisible();

    // Check benefit icons
    const icons = page.locator('.flex-shrink-0.w-8.h-8.rounded-full');
    await expect(icons).toHaveCount(3);
  });

  test('should validate password length', async ({ page }) => {
    await page.goto('/signup.html');

    // Fill short password
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'short');
    await page.fill('#confirmPassword', 'short');
    await page.check('#terms');

    // Try to submit
    await page.click('button[type="submit"]');

    // Browser validation should catch it
    const passwordInput = page.locator('#password');
    const isInvalid = await passwordInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should show password hint', async ({ page }) => {
    await page.goto('/signup.html');

    await expect(page.locator('text=Must be at least 8 characters')).toBeVisible();
  });

  test('should require terms checkbox', async ({ page }) => {
    await page.goto('/signup.html');

    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password123');
    await page.fill('#confirmPassword', 'password123');

    // Don't check terms
    await page.click('button[type="submit"]');

    // Terms checkbox should be invalid
    const termsCheckbox = page.locator('#terms');
    const isInvalid = await termsCheckbox.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should have link to login page', async ({ page }) => {
    await page.goto('/signup.html');

    const loginLink = page.locator('a[href="login.html"]:has-text("Log in")');
    await expect(loginLink).toBeVisible();
  });

  test('should redirect to dashboard if already logged in', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'fake-token-for-redirect-test');
    });

    await page.goto('/signup.html');

    await page.waitForURL('**/dashboard.html', { timeout: 2000 });
  });
});

test.describe('Modernized Frontend - Auth Responsive Design', () => {
  test('login page should be mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login.html');

    // Form should still be visible and usable
    await expect(page.locator('h1:has-text("Welcome back")')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();

    // Card should fit in viewport
    const card = page.locator('.card');
    const cardBox = await card.boundingBox();
    expect(cardBox?.width).toBeLessThanOrEqual(375);
  });

  test('signup page should be mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/signup.html');

    await expect(page.locator('h1:has-text("Create your account")')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();

    // Benefits section should still be visible
    await expect(page.locator('text=Best Prices Guaranteed')).toBeVisible();
  });
});

test.describe('Modernized Frontend - Auth Accessibility', () => {
  test('login form should have proper labels', async ({ page }) => {
    await page.goto('/login.html');

    // Check labels
    await expect(page.locator('label[for="email"]')).toBeVisible();
    await expect(page.locator('label[for="password"]')).toBeVisible();
    await expect(page.locator('label[for="remember"]')).toBeVisible();
  });

  test('signup form should have proper labels', async ({ page }) => {
    await page.goto('/signup.html');

    await expect(page.locator('label[for="email"]')).toBeVisible();
    await expect(page.locator('label[for="password"]')).toBeVisible();
    await expect(page.locator('label[for="confirmPassword"]')).toBeVisible();
    await expect(page.locator('label[for="terms"]')).toBeVisible();
  });

  test('form inputs should have proper autocomplete', async ({ page }) => {
    await page.goto('/login.html');

    const emailInput = page.locator('#email');
    await expect(emailInput).toHaveAttribute('autocomplete', 'email');

    const passwordInput = page.locator('#password');
    await expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
  });
});

test.describe('Modernized Frontend - Auth Error Handling', () => {
  test('should have error message container', async ({ page }) => {
    await page.goto('/login.html');

    const errorEl = page.locator('#error');
    await expect(errorEl).toBeHidden();

    // Check it has error styling classes
    const classes = await errorEl.getAttribute('class');
    expect(classes).toContain('hidden');
    expect(classes).toContain('bg-red-50');
  });

  test('signup should have error message container', async ({ page }) => {
    await page.goto('/signup.html');

    const errorEl = page.locator('#error');
    await expect(errorEl).toBeHidden();
  });
});

test.describe('Modernized Frontend - Auth Loading States', () => {
  test('login button should show loading state on submit', async ({ page }) => {
    await page.goto('/login.html');

    // Fill form with valid data
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password123');

    // Intercept the API call to delay it
    await page.route('**/auth/login', async (route) => {
      await page.waitForTimeout(1000);
      await route.fulfill({
        status: 401,
        body: JSON.stringify({ error: 'Invalid credentials' })
      });
    });

    // Submit form
    await page.click('button[type="submit"]');

    // Check button is disabled and shows spinner
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeDisabled();
  });
});
