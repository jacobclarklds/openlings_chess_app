import { test, expect } from '@playwright/test';

/**
 * Simple test to verify the infrastructure works
 */

test('basic page load test', async ({ page }) => {
  // This test will start the dev server automatically via playwright.config.ts
  await page.goto('/');

  // Just check that the page loads
  await expect(page).toHaveTitle(/Chess/i, { timeout: 10000 });

  console.log('✅ Basic infrastructure test passed');
});

test('demo page loads', async ({ page }) => {
  await page.goto('/demo');

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Check if page is visible
  const body = page.locator('body');
  await expect(body).toBeVisible();

  console.log('✅ Demo page loads successfully');
});
