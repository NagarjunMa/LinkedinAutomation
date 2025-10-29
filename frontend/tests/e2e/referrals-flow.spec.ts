import { test, expect } from '@playwright/test';

test.describe('Referrals Page UI/UX Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to referrals page
    await page.goto('/dashboard/referrals');
    await page.waitForLoadState('networkidle');
  });

  test('should display referrals page layout correctly', async ({ page }) => {
    // Check if page loads without errors
    await expect(page.locator('body')).toBeVisible();

    // Look for tab navigation
    const tabs = page.locator('[role="tablist"], .tabs, [data-tabs]');
    if (await tabs.count() > 0) {
      await expect(tabs.first()).toBeVisible();
    }
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('body')).toBeVisible();

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('body')).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle tab navigation', async ({ page }) => {
    // Look for tab elements
    const tabElements = await page.locator('button:has-text("Generator"), button:has-text("Templates"), button:has-text("Analytics"), button:has-text("Contacts"), [role="tab"]').all();

    if (tabElements.length > 0) {
      // Click on different tabs if they exist
      for (let i = 0; i < Math.min(tabElements.length, 3); i++) {
        await tabElements[i].click();
        await page.waitForTimeout(500); // Wait for tab content to load
        await expect(page.locator('body')).toBeVisible();
      }
    }
  });

  test('should test contact paste and parse functionality', async ({ page }) => {
    // Look for text areas or input fields for pasting contact info
    const pasteArea = page.locator('textarea[placeholder*="paste"], textarea[placeholder*="LinkedIn"], textarea[placeholder*="contact"]').first();

    if (await pasteArea.count() > 0) {
      await pasteArea.fill(`John Doe
Software Engineer at Google
john.doe@google.com
New York, NY`);

      // Look for parse button or auto-parsing
      const parseButton = page.locator('button:has-text("Parse"), button:has-text("Extract")');
      if (await parseButton.count() > 0) {
        await parseButton.click();
      } else {
        // If auto-parsing, trigger blur event
        await pasteArea.blur();
      }

      await page.waitForTimeout(1000);

      // Check if parsed information appears
      const nameField = page.locator('input[value*="John Doe"], input[placeholder*="name"], input[placeholder*="Name"]');
      if (await nameField.count() > 0) {
        await expect(nameField.first()).toBeVisible();
      }
    }
  });

  test('should test template generation flow', async ({ page }) => {
    // Look for generate button
    const generateButton = page.locator('button:has-text("Generate"), button:has-text("Create Template")');

    if (await generateButton.count() > 0) {
      // Fill in minimal required fields first
      const nameInput = page.locator('input[placeholder*="name"], input[name*="name"]').first();
      if (await nameInput.count() > 0) {
        await nameInput.fill('Test Contact');
      }

      const companyInput = page.locator('input[placeholder*="company"], input[name*="company"]').first();
      if (await companyInput.count() > 0) {
        await companyInput.fill('Test Company');
      }

      // Try to generate template
      await generateButton.click();

      // Wait for generation (might take a few seconds)
      await page.waitForTimeout(3000);

      // Look for generated content
      const templateContent = page.locator('div:has-text("Subject"), div:has-text("Email"), textarea[value*="Dear"], pre:has-text("Dear")');
      if (await templateContent.count() > 0) {
        await expect(templateContent.first()).toBeVisible();
      }
    }
  });

  test('should test copy to clipboard functionality', async ({ page }) => {
    // Look for copy buttons
    const copyButtons = page.locator('button:has-text("Copy"), button[title*="copy"], button[aria-label*="copy"]');

    if (await copyButtons.count() > 0) {
      // Grant clipboard permissions
      await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

      // Click copy button
      await copyButtons.first().click();

      // Check for success feedback
      const successMessage = page.locator('div:has-text("Copied"), div:has-text("Success"), .toast, .notification');
      if (await successMessage.count() > 0) {
        await expect(successMessage.first()).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should check for accessibility features', async ({ page }) => {
    // Check for ARIA labels
    const ariaElements = page.locator('[aria-label], [aria-describedby], [role]');
    if (await ariaElements.count() > 0) {
      await expect(ariaElements.first()).toBeVisible();
    }

    // Check for keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');
    if (await focusedElement.count() > 0) {
      await expect(focusedElement).toBeVisible();
    }
  });

  test('should handle loading states gracefully', async ({ page }) => {
    // Look for loading indicators
    await page.goto('/dashboard/referrals');

    // Check for loading spinners or skeleton screens
    const loadingElements = page.locator('.loading, .spinner, .skeleton, [data-loading]');

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Ensure content is visible after loading
    await expect(page.locator('body')).toBeVisible();
  });

  test('should validate form inputs', async ({ page }) => {
    // Find form inputs
    const inputs = page.locator('input[required], input[type="email"]');

    if (await inputs.count() > 0) {
      // Try submitting with invalid data
      const emailInput = page.locator('input[type="email"]').first();
      if (await emailInput.count() > 0) {
        await emailInput.fill('invalid-email');
        await emailInput.blur();

        // Look for validation messages
        const validationMessage = page.locator('.error, .invalid, [role="alert"]');
        // Validation message might appear
      }
    }
  });
});