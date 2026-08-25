import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

export class InsightsPage extends BasePage {
  readonly header: Locator;
  readonly filterDropdown: Locator;
  readonly sortDropdown: Locator;
  readonly insightsGrid: Locator;
  readonly insightCards: Locator;
  readonly pagination: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.locator('h1:has-text("Insights")');
    this.filterDropdown = page.locator('select:has-text("Type"), [data-testid="filter-type"]');
    this.sortDropdown = page.locator('select:has-text("Sort"), [data-testid="sort"]');
    this.insightsGrid = page.locator('[data-testid="insights-grid"], .grid');
    this.insightCards = page.locator('[data-testid="insight-card"], [class*="insight"]');
    this.pagination = page.locator('[data-testid="pagination"]');
    this.emptyState = page.locator('[data-testid="empty-state"]');
  }

  async goto() {
    await this.page.goto('/insights');
    await this.page.waitForLoadState('networkidle');
  }

  async filterByType(type: string) {
    await this.filterDropdown.selectOption(type);
    await this.waitForLoading();
  }

  async sortBy(sortOption: string) {
    await this.sortDropdown.selectOption(sortOption);
    await this.waitForLoading();
  }

  async clickInsightCard(index: number = 0) {
    await this.insightCards.nth(index).click();
  }

  async expectInsightCount(count: number) {
    await expect(this.insightCards).toHaveCount(count);
  }

  async expectPaginationVisible() {
    await expect(this.pagination).toBeVisible();
  }

  async clickFeedbackButton(cardIndex: number, helpful: boolean) {
    const feedbackButtons = this.insightCards.nth(cardIndex).locator('button');
    await (helpful ? feedbackButtons.first() : feedbackButtons.last()).click();
  }
}
