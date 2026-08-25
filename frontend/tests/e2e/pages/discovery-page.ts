import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

export class DiscoveryPage extends BasePage {
  readonly header: Locator;
  readonly flowTypeSelector: Locator;
  readonly bentoGrid: Locator;
  readonly timeline: Locator;
  readonly spotlight: Locator;
  readonly flowCards: Locator;
  readonly startFlowButton: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.locator('h1:has-text("Discovery")');
    this.flowTypeSelector = page.locator('[data-testid="flow-type"], select');
    this.bentoGrid = page.locator('[data-testid="bento-grid"], .bento-grid');
    this.timeline = page.locator('[data-testid="timeline"], .timeline');
    this.spotlight = page.locator('[data-testid="spotlight"], .spotlight');
    this.flowCards = page.locator('[data-testid="flow-card"], [class*="flow"]');
    this.startFlowButton = page.locator('button:has-text("Start"), button:has-text("Begin")');
  }

  async goto() {
    await this.page.goto('/discovery');
    await this.page.waitForLoadState('networkidle');
  }

  async selectFlowType(flowType: string) {
    await this.flowTypeSelector.selectOption(flowType);
    await this.waitForLoading();
  }

  async clickFlowCard(index: number = 0) {
    await this.flowCards.nth(index).click();
  }

  async startDiscoveryFlow() {
    await this.startFlowButton.click();
  }

  async expectFlowCount(count: number) {
    await expect(this.flowCards).toHaveCount(count);
  }

  async expectTimelineVisible() {
    await expect(this.timeline).toBeVisible();
  }

  async expectBentoGridVisible() {
    await expect(this.bentoGrid).toBeVisible();
  }
}
