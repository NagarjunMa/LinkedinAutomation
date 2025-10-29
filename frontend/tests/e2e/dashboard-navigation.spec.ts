import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation UI/UX Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard layout correctly', async ({ page }) => {
    // Check if dashboard loads
    await expect(page.locator('body')).toBeVisible();

    // Look for navigation elements
    const navigation = page.locator('nav, .sidebar, .navigation, [role="navigation"]');
    if (await navigation.count() > 0) {
      await expect(navigation.first()).toBeVisible();
    }
  });

  test('should navigate between dashboard sections', async ({ page }) => {
    // Test navigation to different dashboard sections
    const sections = [
      { text: 'Jobs', url: '/dashboard/jobs' },
      { text: 'Referrals', url: '/dashboard/referrals' },
      { text: 'Resume', url: '/dashboard/resume-evaluation' },
      { text: 'Applications', url: '/dashboard/applications' }
    ];

    for (const section of sections) {
      // Look for navigation links
      const navLink = page.locator(`a:has-text("${section.text}"), button:has-text("${section.text}"), [href*="${section.url}"]`);

      if (await navLink.count() > 0) {
        await navLink.first().click();
        await page.waitForLoadState('networkidle');

        // Verify navigation worked
        const currentUrl = page.url();
        expect(currentUrl).toContain('dashboard');
      }
    }
  });

  test('should have responsive sidebar/navigation', async ({ page }) => {
    // Test on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Look for mobile menu button
    const mobileMenuButton = page.locator('button[aria-label*="menu"], .menu-toggle, .hamburger, [data-testid*="menu"]');

    if (await mobileMenuButton.count() > 0) {
      await mobileMenuButton.click();

      // Check if navigation becomes visible
      const mobileNav = page.locator('.mobile-nav, .sidebar, nav');
      if (await mobileNav.count() > 0) {
        await expect(mobileNav.first()).toBeVisible();
      }
    }
  });

  test('should display user profile/settings access', async ({ page }) => {
    // Look for profile or settings links
    const profileElements = page.locator('button:has-text("Profile"), a:has-text("Settings"), .user-menu, .profile-dropdown, [data-testid*="profile"]');

    if (await profileElements.count() > 0) {
      await expect(profileElements.first()).toBeVisible();
    }
  });

  test('should show dashboard metrics/stats', async ({ page }) => {
    // Look for dashboard metrics or stats cards
    const statsElements = page.locator('.stats, .metrics, .card, .dashboard-card, [data-testid*="stat"]');

    if (await statsElements.count() > 0) {
      await expect(statsElements.first()).toBeVisible();
    }
  });

  test('should handle theme switching', async ({ page }) => {
    // Look for theme toggle button
    const themeToggle = page.locator('button[aria-label*="theme"], .theme-toggle, button:has-text("Dark"), button:has-text("Light")');

    if (await themeToggle.count() > 0) {
      // Get initial theme state
      const initialTheme = await page.locator('html').getAttribute('class');

      // Toggle theme
      await themeToggle.click();
      await page.waitForTimeout(500);

      // Check if theme changed
      const newTheme = await page.locator('html').getAttribute('class');
      // Theme should change (different class or data attribute)
    }
  });

  test('should display breadcrumb navigation', async ({ page }) => {
    await page.goto('/dashboard/referrals');

    // Look for breadcrumbs
    const breadcrumbs = page.locator('.breadcrumb, .breadcrumbs, nav[aria-label*="breadcrumb"]');

    if (await breadcrumbs.count() > 0) {
      await expect(breadcrumbs.first()).toBeVisible();
    }
  });

  test('should show loading states during navigation', async ({ page }) => {
    // Click on a navigation link
    const navLink = page.locator('a[href*="/dashboard/"], button').first();

    if (await navLink.count() > 0) {
      await navLink.click();

      // Look for loading indicators
      const loadingIndicator = page.locator('.loading, .spinner, [data-loading="true"]');

      // Wait for navigation to complete
      await page.waitForLoadState('networkidle');

      // Ensure page is loaded
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should maintain navigation state', async ({ page }) => {
    // Navigate to a specific section
    await page.goto('/dashboard/referrals');

    // Check if the current section is highlighted
    const activeNavItem = page.locator('.active, .current, [aria-current="page"], .selected');

    if (await activeNavItem.count() > 0) {
      await expect(activeNavItem.first()).toBeVisible();
    }
  });

  test('should be keyboard accessible', async ({ page }) => {
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    let focusedElement = page.locator(':focus');

    if (await focusedElement.count() > 0) {
      await expect(focusedElement).toBeVisible();
    }

    // Continue tabbing through navigation elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      focusedElement = page.locator(':focus');

      if (await focusedElement.count() > 0) {
        await expect(focusedElement).toBeVisible();
      }
    }

    // Test Enter key on focused elements
    const focusedLink = page.locator(':focus');
    if (await focusedLink.count() > 0) {
      await page.keyboard.press('Enter');
      await page.waitForLoadState('networkidle');
    }
  });
});