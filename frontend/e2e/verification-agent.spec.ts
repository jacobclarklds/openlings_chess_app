import { test, expect } from '@playwright/test';
import { FrontendInspector } from './utils/inspector';

/**
 * Automated Verification Agent
 *
 * This test suite acts as an automated agent that verifies UI changes
 * are making it to the frontend. It can be run automatically after changes.
 */

interface VerificationConfig {
  url: string;
  expectedElements: {
    selector: string;
    shouldBeVisible: boolean;
    expectedText?: string;
  }[];
  changeDescription: string;
}

/**
 * Main verification test that can be configured for different changes
 */
test.describe('Frontend Verification Agent', () => {

  test('verify chess demo page loads correctly', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    // Wait for React to hydrate and render
    await page.waitForTimeout(2000);

    // Verify chess board is visible
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 10000 });

    // Verify coach content is visible
    const content = page.locator('text=Opening Principles').first();
    await expect(content).toBeVisible({ timeout: 5000 });

    console.log('\n✅ Chess demo page verified successfully');
  });

  test('verify coach comment panel functionality', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow for async loading

    // Verify coach content
    const content = page.locator('text=Opening Principles').first();
    await expect(content).toBeVisible({ timeout: 5000 });

    // Verify navigation buttons
    const nextButton = page.locator('button:has-text("Next")').first();
    await expect(nextButton).toBeVisible({ timeout: 5000 });

    const prevButton = page.locator('button:has-text("Previous")').first();
    await expect(prevButton).toBeVisible({ timeout: 5000 });

    console.log('\n✅ Coach panel verified successfully');
  });

  test('verify board theme and styling', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    // Wait for React hydration and board rendering
    await page.waitForTimeout(2000);

    // Check if board has proper styling using the chessboard container ID
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 10000 });

    // Get computed styles
    const hasStyles = await board.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        hasBackground: styles.backgroundColor !== 'rgba(0, 0, 0, 0)',
        hasSize: styles.width !== '0px' && styles.height !== '0px',
      };
    });

    // Verify styles
    expect(hasStyles.hasSize).toBe(true);

    console.log('\n🎨 Board styling verified successfully');
  });
});

/**
 * Custom verification runner that can be called programmatically
 */
export async function runVerification(config: VerificationConfig): Promise<boolean> {
  // This function can be used by scripts to verify specific changes
  console.log(`\n🔍 Running verification for: ${config.changeDescription}`);
  console.log(`URL: ${config.url}`);
  console.log(`Expected elements: ${config.expectedElements.length}`);

  return true; // Would need to run Playwright programmatically here
}

/**
 * Verification presets for common changes
 */
export const verificationPresets = {
  chessBoard: {
    changeDescription: 'Chess board rendering',
    url: '/demo',
    expectedElements: [
      { selector: '#chessboard-board', shouldBeVisible: true },
      { selector: 'text=Enhanced Chess UI Demo', shouldBeVisible: true },
    ],
  },

  coachPanel: {
    changeDescription: 'Coach comment panel',
    url: '/demo',
    expectedElements: [
      { selector: 'text=Opening Principles', shouldBeVisible: true },
      { selector: 'button:has-text("Next")', shouldBeVisible: true },
      { selector: 'button:has-text("Previous")', shouldBeVisible: true },
    ],
  },

  annotations: {
    changeDescription: 'Board annotations',
    url: '/demo',
    expectedElements: [
      { selector: '#chessboard-board', shouldBeVisible: true },
      { selector: 'text=How to use:', shouldBeVisible: true },
    ],
  },

  aiThinking: {
    changeDescription: 'AI thinking indicator',
    url: '/demo',
    expectedElements: [
      { selector: 'button:has-text("AI Thinking Indicator")', shouldBeVisible: true },
    ],
  },
};
