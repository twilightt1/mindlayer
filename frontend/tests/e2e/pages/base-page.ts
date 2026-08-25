import { Page, Locator, expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"], .animate-spin, .loading');
    this.errorMessage = page.locator('[data-testid="error-message"], .error, [role="alert"]');
    this.emptyState = page.locator('[data-testid="empty-state"], .empty-state');
  }

  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  async waitForLoading() {
    await this.page.waitForSelector(this.loadingSpinner, { state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async expectNoError() {
    await expect(this.errorMessage).not.toBeVisible();
  }

  async expectToBeVisible(locator: Locator) {
    await expect(locator).toBeVisible();
  }

  async getTextContent(locator: Locator): Promise<string> {
    return locator.textContent() ?? '';
  }
}
