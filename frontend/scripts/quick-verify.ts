#!/usr/bin/env node

/**
 * Quick Verification Script
 * Can be run programmatically to verify specific UI elements
 *
 * Usage:
 *   npm run verify:quick
 *   npm run verify:quick -- --preset=chessBoard
 *   npm run verify:quick -- --url=/demo --selector=".chessboard"
 */

import { chromium, Browser, Page } from '@playwright/test';

interface QuickVerifyOptions {
  url?: string;
  selectors?: string[];
  preset?: string;
  timeout?: number;
}

const presets: Record<string, QuickVerifyOptions> = {
  chessBoard: {
    url: '/demo',
    selectors: ['#chessboard-board', 'text=Enhanced Chess UI Demo'],
    timeout: 10000,
  },
  coachPanel: {
    url: '/demo',
    selectors: ['text=Opening Principles', 'button:has-text("Next")'],
    timeout: 5000,
  },
  fullPage: {
    url: '/demo',
    selectors: [
      '#chessboard-board',
      'text=Opening Principles',
      'button:has-text("Next")',
    ],
    timeout: 10000,
  },
};

async function quickVerify(options: QuickVerifyOptions): Promise<boolean> {
  let browser: Browser | null = null;
  let allPassed = true;

  try {
    console.log('\n🚀 Quick Frontend Verification');
    console.log('================================\n');

    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    const baseURL = 'http://localhost:3000';
    const url = options.url || '/';
    const fullURL = `${baseURL}${url}`;

    console.log(`📍 Navigating to: ${fullURL}`);
    await page.goto(fullURL, { waitUntil: 'networkidle' });

    const selectors = options.selectors || [];
    console.log(`🔍 Checking ${selectors.length} element(s)...\n`);

    for (const selector of selectors) {
      try {
        const element = page.locator(selector).first();
        const isVisible = await element.isVisible({ timeout: options.timeout || 5000 });

        if (isVisible) {
          console.log(`✅ ${selector} - VISIBLE`);
        } else {
          console.log(`❌ ${selector} - NOT VISIBLE`);
          allPassed = false;
        }
      } catch (error) {
        console.log(`❌ ${selector} - NOT FOUND`);
        allPassed = false;
      }
    }

    // Capture screenshot
    const screenshotPath = `test-results/quick-verify-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`\n📸 Screenshot saved: ${screenshotPath}`);

    // Check for console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    if (consoleErrors.length > 0) {
      console.log('\n⚠️  Console errors detected:');
      consoleErrors.forEach(err => console.log(`   ${err}`));
    }

    await browser.close();

    console.log('\n================================');
    if (allPassed) {
      console.log('✅ All checks passed!\n');
    } else {
      console.log('❌ Some checks failed\n');
    }

    return allPassed;

  } catch (error) {
    console.error('\n❌ Verification failed with error:');
    console.error(error);

    if (browser) {
      await browser.close();
    }

    return false;
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const options: QuickVerifyOptions = {
  selectors: [],
};

for (let i = 0; i < args.length; i++) {
  const arg = args[i];

  if (arg.startsWith('--preset=')) {
    const presetName = arg.split('=')[1];
    const preset = presets[presetName];
    if (preset) {
      Object.assign(options, preset);
      console.log(`Using preset: ${presetName}`);
    } else {
      console.error(`Unknown preset: ${presetName}`);
      console.error(`Available presets: ${Object.keys(presets).join(', ')}`);
      process.exit(1);
    }
  } else if (arg.startsWith('--url=')) {
    options.url = arg.split('=')[1];
  } else if (arg.startsWith('--selector=')) {
    options.selectors!.push(arg.split('=')[1]);
  } else if (arg.startsWith('--timeout=')) {
    options.timeout = parseInt(arg.split('=')[1], 10);
  }
}

// Default to fullPage preset if nothing specified
if (!options.url && options.selectors!.length === 0) {
  Object.assign(options, presets.fullPage);
}

// Run verification
quickVerify(options).then(passed => {
  process.exit(passed ? 0 : 1);
});
