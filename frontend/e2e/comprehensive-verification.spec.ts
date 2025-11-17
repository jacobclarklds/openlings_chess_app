import { test, expect } from '@playwright/test';

/**
 * Comprehensive UI Verification
 * Tests that actually validate the QUALITY of the UI, not just that elements exist
 */

test.describe('Comprehensive Chess UI Verification', () => {

  test('visual quality - chess board has proper styling', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible();

    // Check computed styles
    const styles = await board.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        display: computed.display,
        width: computed.width,
        height: computed.height,
        position: computed.position,
      };
    });

    // Verify it's actually rendered as a grid
    expect(styles.display).toBe('grid');

    // Verify it has actual dimensions (not 0x0)
    expect(parseInt(styles.width)).toBeGreaterThan(0);
    expect(parseInt(styles.height)).toBeGreaterThan(0);

    // Check that squares have the right colors
    const lightSquare = page.locator('#chessboard-square-a1').first();
    const darkSquare = page.locator('#chessboard-square-a8').first();

    const lightBg = await lightSquare.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );
    const darkBg = await darkSquare.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );

    // Colors should be different
    expect(lightBg).not.toBe(darkBg);

    console.log('✅ Chess board styling verified');
  });

  test('visual quality - coach panel has styled content', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check for the coach content
    const heading = page.locator('h2:has-text("Opening Principles")').first();
    await expect(heading).toBeVisible();

    // Verify heading has color styling
    const headingColor = await heading.evaluate((el) =>
      window.getComputedStyle(el).color
    );

    // Should not be default black (rgb(0, 0, 0))
    expect(headingColor).not.toBe('rgb(0, 0, 0)');

    // Check that list items are visible
    const listItems = page.locator('text=Control the center').first();
    await expect(listItems).toBeVisible();

    console.log('✅ Coach panel styling verified');
  });

  test('functionality - navigation buttons work', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const prevButton = page.locator('button:has-text("Previous")').first();
    const nextButton = page.locator('button:has-text("Next")').first();

    // Previous button should be disabled at start (Step 1 of 1)
    await expect(prevButton).toBeDisabled();

    // Next button should also be disabled (only 1 step in demo)
    await expect(nextButton).toBeDisabled();

    console.log('✅ Navigation buttons verified');
  });

  test('functionality - AI thinking indicator toggles', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const toggleButton = page.locator('button:has-text("AI Thinking Indicator")').first();
    await expect(toggleButton).toBeVisible();

    // Click to show
    await toggleButton.click();
    await page.waitForTimeout(500);

    // Button text should change
    await expect(toggleButton).toContainText('Hide');

    // Click to hide
    await toggleButton.click();
    await page.waitForTimeout(500);

    await expect(toggleButton).toContainText('Show');

    console.log('✅ AI thinking indicator toggle verified');
  });

  test('responsive design - layout adapts to viewport', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible();

    const coachContent = page.locator('text=Opening Principles').first();
    await expect(coachContent).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);

    await expect(board).toBeVisible();
    await expect(coachContent).toBeVisible();

    console.log('✅ Responsive design verified');
  });

  test('no console errors - page loads cleanly', async ({ page }) => {
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Log any errors/warnings for debugging
    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }
    if (consoleWarnings.length > 0) {
      console.log('Console warnings:', consoleWarnings);
    }

    // Should have no errors
    expect(consoleErrors.length).toBe(0);

    console.log('✅ No console errors detected');
  });

  test('accessibility - key elements have proper attributes', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check that buttons have accessible text
    const toggleButton = page.locator('button:has-text("AI Thinking Indicator")').first();
    const buttonText = await toggleButton.textContent();
    expect(buttonText?.trim().length).toBeGreaterThan(0);

    // Check that navigation buttons are properly labeled
    const nextButton = page.locator('button:has-text("Next")').first();
    const prevButton = page.locator('button:has-text("Previous")').first();

    await expect(nextButton).toHaveText(/Next/);
    await expect(prevButton).toHaveText(/Previous/);

    console.log('✅ Accessibility checks passed');
  });

  test('performance - page loads reasonably fast', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Page should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);

    // Board should be visible quickly
    const board = page.locator('#chessboard-board').first();
    await expect(board).toBeVisible({ timeout: 3000 });

    console.log(`✅ Page loaded in ${loadTime}ms`);
  });

  test('content quality - coach panel has meaningful content', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check that the coach content is not empty
    const content = page.locator('text=Opening Principles').first();
    const parent = content.locator('..').first();
    const text = await parent.textContent();

    // Should have substantial content (more than just a heading)
    expect(text?.length || 0).toBeGreaterThan(50);

    // Should contain expected keywords
    expect(text).toContain('center');
    expect(text).toContain('pieces');

    console.log('✅ Coach content quality verified');
  });

  test('visual polish - page has proper styling', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const body = page.locator('body');
    const bodyBg = await body.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );

    // Should have a background color (not default white)
    expect(bodyBg).not.toBe('rgb(255, 255, 255)');

    // Check for gradient on main container
    const mainContainer = page.locator('.min-h-screen').first();
    const bgImage = await mainContainer.evaluate((el) =>
      window.getComputedStyle(el).backgroundImage
    );

    // Should have a gradient background
    expect(bgImage).toContain('gradient');

    console.log('✅ Visual polish verified');
  });
});
