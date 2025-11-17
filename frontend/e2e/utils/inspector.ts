import { Page, BrowserContext } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Frontend Inspector Utility
 * Captures and analyzes the state of the frontend for verification
 */

export interface InspectionReport {
  timestamp: string;
  url: string;
  testName: string;
  passed: boolean;
  screenshots: {
    fullPage?: string;
    viewport?: string;
  };
  dom: {
    html: string;
    elements: ElementSummary[];
  };
  network: {
    requests: NetworkRequest[];
    errors: string[];
  };
  console: {
    logs: string[];
    errors: string[];
    warnings: string[];
  };
  assertions: AssertionResult[];
}

export interface ElementSummary {
  selector: string;
  text?: string;
  visible: boolean;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface NetworkRequest {
  url: string;
  method: string;
  status?: number;
  timing?: number;
}

export interface AssertionResult {
  name: string;
  passed: boolean;
  message?: string;
  expected?: any;
  actual?: any;
}

export class FrontendInspector {
  private page: Page;
  private testName: string;
  private consoleMessages: string[] = [];
  private consoleErrors: string[] = [];
  private consoleWarnings: string[] = [];
  private networkRequests: NetworkRequest[] = [];
  private networkErrors: string[] = [];

  constructor(page: Page, testName: string) {
    this.page = page;
    this.testName = testName;
    this.setupListeners();
  }

  private setupListeners() {
    // Console listeners
    this.page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();

      if (type === 'error') {
        this.consoleErrors.push(text);
      } else if (type === 'warning') {
        this.consoleWarnings.push(text);
      } else {
        this.consoleMessages.push(text);
      }
    });

    // Network listeners
    this.page.on('request', request => {
      this.networkRequests.push({
        url: request.url(),
        method: request.method(),
      });
    });

    this.page.on('response', response => {
      const request = this.networkRequests.find(r => r.url === response.url());
      if (request) {
        request.status = response.status();
      }
    });

    this.page.on('requestfailed', request => {
      this.networkErrors.push(`Failed: ${request.url()} - ${request.failure()?.errorText}`);
    });
  }

  /**
   * Inspect specific elements on the page
   */
  async inspectElements(selectors: string[]): Promise<ElementSummary[]> {
    const elements: ElementSummary[] = [];

    for (const selector of selectors) {
      try {
        const element = this.page.locator(selector).first();
        const isVisible = await element.isVisible().catch(() => false);
        const text = await element.textContent().catch(() => undefined);
        const box = await element.boundingBox().catch(() => undefined);

        elements.push({
          selector,
          text: text || undefined,
          visible: isVisible,
          boundingBox: box || undefined,
        });
      } catch (error) {
        elements.push({
          selector,
          visible: false,
        });
      }
    }

    return elements;
  }

  /**
   * Take screenshots for documentation
   */
  async captureScreenshots(): Promise<{ fullPage?: string; viewport?: string }> {
    const screenshotDir = path.join(process.cwd(), 'test-results', 'screenshots');
    await fs.mkdir(screenshotDir, { recursive: true });

    const timestamp = Date.now();
    const fullPagePath = path.join(screenshotDir, `${this.testName}-full-${timestamp}.png`);
    const viewportPath = path.join(screenshotDir, `${this.testName}-viewport-${timestamp}.png`);

    await this.page.screenshot({ path: fullPagePath, fullPage: true });
    await this.page.screenshot({ path: viewportPath, fullPage: false });

    return {
      fullPage: fullPagePath,
      viewport: viewportPath,
    };
  }

  /**
   * Generate a comprehensive inspection report
   */
  async generateReport(assertions: AssertionResult[] = []): Promise<InspectionReport> {
    const screenshots = await this.captureScreenshots();
    const html = await this.page.content();

    // Default elements to check
    const defaultSelectors = [
      '#chessboard-board',
      'text=Opening Principles',
      'button:has-text("Next")',
      'button',
      'input',
    ];

    const elements = await this.inspectElements(defaultSelectors);

    const report: InspectionReport = {
      timestamp: new Date().toISOString(),
      url: this.page.url(),
      testName: this.testName,
      passed: assertions.every(a => a.passed),
      screenshots,
      dom: {
        html,
        elements,
      },
      network: {
        requests: this.networkRequests,
        errors: this.networkErrors,
      },
      console: {
        logs: this.consoleMessages,
        errors: this.consoleErrors,
        warnings: this.consoleWarnings,
      },
      assertions,
    };

    // Save report to file
    await this.saveReport(report);

    return report;
  }

  /**
   * Save report to JSON file
   */
  private async saveReport(report: InspectionReport) {
    const reportDir = path.join(process.cwd(), 'test-results', 'inspection-reports');
    await fs.mkdir(reportDir, { recursive: true });

    const timestamp = Date.now();
    const reportPath = path.join(reportDir, `${this.testName}-${timestamp}.json`);

    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`Inspection report saved: ${reportPath}`);
  }

  /**
   * Verify specific UI elements exist and are visible
   */
  async verifyUIElements(elements: { selector: string; shouldBeVisible: boolean }[]): Promise<AssertionResult[]> {
    const results: AssertionResult[] = [];

    for (const { selector, shouldBeVisible } of elements) {
      try {
        const element = this.page.locator(selector).first();
        const isVisible = await element.isVisible().catch(() => false);

        results.push({
          name: `Element visibility: ${selector}`,
          passed: isVisible === shouldBeVisible,
          expected: shouldBeVisible,
          actual: isVisible,
          message: isVisible === shouldBeVisible
            ? `Element ${selector} visibility is correct`
            : `Element ${selector} expected to be ${shouldBeVisible ? 'visible' : 'hidden'} but was ${isVisible ? 'visible' : 'hidden'}`,
        });
      } catch (error) {
        results.push({
          name: `Element visibility: ${selector}`,
          passed: false,
          expected: shouldBeVisible,
          actual: false,
          message: `Error checking element: ${error}`,
        });
      }
    }

    return results;
  }

  /**
   * Check for console errors
   */
  hasConsoleErrors(): boolean {
    return this.consoleErrors.length > 0;
  }

  /**
   * Check for network errors
   */
  hasNetworkErrors(): boolean {
    return this.networkErrors.length > 0;
  }

  /**
   * Get summary of issues
   */
  getIssuesSummary(): string {
    const issues: string[] = [];

    if (this.consoleErrors.length > 0) {
      issues.push(`Console Errors (${this.consoleErrors.length}):`);
      this.consoleErrors.forEach(err => issues.push(`  - ${err}`));
    }

    if (this.networkErrors.length > 0) {
      issues.push(`Network Errors (${this.networkErrors.length}):`);
      this.networkErrors.forEach(err => issues.push(`  - ${err}`));
    }

    return issues.length > 0 ? issues.join('\n') : 'No issues detected';
  }
}

/**
 * Helper to create an inspector for a test
 */
export function createInspector(page: Page, testName: string): FrontendInspector {
  return new FrontendInspector(page, testName);
}
