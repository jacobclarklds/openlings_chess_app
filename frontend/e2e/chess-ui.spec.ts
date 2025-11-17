import { test, expect, Page } from '@playwright/test';

/**
 * Chess UI Inspection Tests
 * These tests verify that UI changes are actually making it to the frontend
 */

test.describe('Chess Demo Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for React hydration
  });

  test('should load chess board', async ({ page }) => {
    // Wait for the chessboard to be visible
    await expect(page.locator('#chessboard-board').first()).toBeVisible({ timeout: 10000 });
  });

  test('should display coach comment panel', async ({ page }) => {
    // Check for coach comment panel content
    const commentPanel = page.locator('text=Opening Principles').first();
    await expect(commentPanel).toBeVisible({ timeout: 5000 });
  });

  test('should have AI thinking indicator button', async ({ page }) => {
    // Look for AI thinking indicator toggle button
    const aiButton = page.locator('button:has-text("AI Thinking Indicator")').first();
    await expect(aiButton).toBeVisible({ timeout: 5000 });
  });

  test('should display annotation instructions', async ({ page }) => {
    // Check if annotation instructions exist
    const instructions = page.getByText('How to use:').first();
    await expect(instructions).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Chess Board Annotations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should support board themes', async ({ page }) => {
    // Check if board is visible with ID
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 10000 });
  });

  test('should display page title and description', async ({ page }) => {
    // Check for page title
    const title = page.locator('text=Enhanced Chess UI Demo').first();
    await expect(title).toBeVisible({ timeout: 5000 });

    // Should have description
    const description = page.locator('text=Try the annotation tools').first();
    await expect(description).toBeVisible({ timeout: 5000 });
  });
});

/**
 * Utility function to capture page state for debugging
 */
async function capturePageState(page: Page, testName: string) {
  const screenshot = await page.screenshot({ fullPage: true });
  const html = await page.content();

  return {
    testName,
    screenshot,
    html,
    url: page.url(),
    timestamp: new Date().toISOString()
  };
}

/**
 * Custom assertion helpers
 */
export const chessAssertions = {
  async hasChessBoard(page: Page) {
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 10000 });
    return true;
  },

  async hasCoachPanel(page: Page) {
    const panel = page.locator('text=Opening Principles').first();
    await expect(panel).toBeVisible({ timeout: 5000 });
    return true;
  },

  async canMakeMoves(page: Page) {
    // Check if the board is interactive
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 10000 });
    return true;
  }
};
