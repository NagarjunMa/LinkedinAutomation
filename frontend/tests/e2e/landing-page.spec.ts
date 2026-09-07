import { test, expect } from '@playwright/test';

test.describe('Landing Page UI/UX Tests', () => {
  test('should load landing page successfully', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    // Check for page title
    await expect(page).toHaveTitle(/PrismPro/);

    // Check for main content visibility
    await expect(page.locator('body')).toBeVisible();
    await expect(page.getByRole('heading', { name: /make the work behind your resume visible/i })).toBeVisible();
    await expect(page.getByRole('form', { name: /join the prismpro private preview from the hero/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /sign in/i })).toHaveCount(0);
  });

  test('submits the secure waitlist without creating an account', async ({ page }) => {
    let submittedPayload: Record<string, unknown> | null = null;
    const analyticsPayloads: Record<string, unknown>[] = [];
    await page.route('**/api/v1/public-preview/events', async (route) => {
      analyticsPayloads.push(route.request().postDataJSON());
      await route.fulfill({ status: 204, body: '' });
    });
    await page.route('**/api/v1/waitlist', async (route) => {
      submittedPayload = route.request().postDataJSON();
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          message: "You're on the list. We'll be in touch when there is a useful next step.",
        }),
      });
    });
    await page.goto('/', { waitUntil: 'networkidle' });

    const form = page.getByRole('form', { name: /from the hero/i });
    await form.getByLabel(/work email/i).fill('candidate@example.com');
    await form.getByRole('checkbox').check();
    await form.getByRole('button', { name: /join the preview/i }).click();

    await expect(page.getByRole('status')).toContainText("You're on the list");
    expect(submittedPayload).toMatchObject({
      email: 'candidate@example.com',
      consent: true,
    });
    await expect.poll(() => analyticsPayloads.map((event) => event.event_name)).toEqual(
      expect.arrayContaining(['form_start', 'hero_cta', 'form_success']),
    );
    expect(JSON.stringify(analyticsPayloads)).not.toContain('candidate@example.com');
  });

  test('requires waitlist consent before sending a request', async ({ page }) => {
    let requestCount = 0;
    await page.route('**/api/v1/waitlist', async (route) => {
      requestCount += 1;
      await route.abort();
    });
    await page.goto('/', { waitUntil: 'networkidle' });

    const form = page.getByRole('form', { name: /from the hero/i });
    await form.getByLabel(/work email/i).fill('candidate@example.com');
    await form.getByRole('button', { name: /join the preview/i }).click();

    await expect(form.getByRole('alert')).toContainText(/please confirm/i);
    expect(requestCount).toBe(0);
  });

  test('should have responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/', { waitUntil: 'networkidle' });

    // Check if page is still functional on mobile
    await expect(page.locator('body')).toBeVisible();
    await expect(page.getByRole('form', { name: /from the hero/i })).toBeVisible();
  });

  test('supports keyboard theme control and reduced-motion preferences', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('prism-theme', 'dark'));
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/', { waitUntil: 'networkidle' });

    await expect(page.locator('html')).toHaveClass(/dark/);
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.focus();
    await expect(themeToggle).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveClass(/light/);

    const audienceMarquee = page
      .locator('[aria-label="People Prism Pro is being designed for"]')
      .locator('[class*="animate-"]');
    await expect(audienceMarquee).toHaveCSS('animation-name', 'none');
  });

  test('honors the system dark-theme preference', async ({ page, browserName }) => {
    test.skip(
      browserName === 'firefox',
      'Playwright Firefox on macOS does not preserve colorScheme emulation across navigation.',
    );
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/', { waitUntil: 'networkidle' });

    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('should keep login and dashboard access closed during public preview', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'networkidle' });
    await expect(page).toHaveURL('/');

    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    await expect(page).toHaveURL('/');
    await expect(page.getByText(/public access closed/i)).toBeVisible();
  });

  test('should have proper meta tags for SEO', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    // Check for viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toBeTruthy();
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
      'content',
      /opengraph-image/,
    );
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
      'content',
      'summary_large_image',
    );
    const structuredData = page.locator(
      'script#prismpro-structured-data[type="application/ld+json"]',
    );
    await expect(structuredData).toHaveCount(1);
    expect(JSON.parse((await structuredData.textContent()) ?? '{}')).toMatchObject({
      '@type': 'SoftwareApplication',
      name: 'PrismPro',
    });
  });
});
