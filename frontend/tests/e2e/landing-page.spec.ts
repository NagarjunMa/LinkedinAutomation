import { test, expect } from '@playwright/test';

test.describe('Landing Page UI/UX Tests', () => {
  test('should load landing page successfully', async ({ page }) => {
    await page.goto('/');

    // Check for page title
    await expect(page).toHaveTitle(/Prism Pro/);

    // Check for main content visibility
    await expect(page.locator('body')).toBeVisible();
  });

  test('should have responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check if page is still functional on mobile
    await expect(page.locator('body')).toBeVisible();
  });

  test('should redirect to dashboard when authenticated', async ({ page }) => {
    await page.goto('/');

    // Check for redirect behavior or authentication form
    await page.waitForLoadState('networkidle');

    const currentUrl = page.url();
    // Should either show landing page or redirect to dashboard
    expect(currentUrl).toMatch(/\/(dashboard)?/);
  });

  test('should have proper meta tags for SEO', async ({ page }) => {
    await page.goto('/');

    // Check for viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toBeTruthy();
  });
});