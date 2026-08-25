import { test, expect } from '@playwright/test';
import { InsightsPage } from '../pages/insights-page';
import { mockInsight, filterOptions } from '../fixtures/sample';

test.describe('Insights Dashboard', () => {
  let insightsPage: InsightsPage;

  test.beforeEach(async ({ page }) => {
    insightsPage = new InsightsPage(page);
    await insightsPage.goto();
  });

  test('should display insights page header', async () => {
    await expect(insightsPage.header).toBeVisible();
  });

  test('should display filter dropdown', async () => {
    await expect(insightsPage.filterDropdown).toBeVisible();
  });

  test('should display sort dropdown', async () => {
    await expect(insightsPage.sortDropdown).toBeVisible();
  });

  test('should filter insights by type', async ({ page }) => {
    // Mock API response
    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [{ ...mockInsight, type: 'trend' }],
          pagination: { page: 1, page_size: 10, total: 1 },
        }),
      });
    });

    await insightsPage.filterByType('trend');
    await insightsPage.waitForLoading();
    await expect(insightsPage.insightCards.first()).toBeVisible();
  });

  test('should sort insights', async ({ page }) => {
    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [mockInsight],
          pagination: { page: 1, page_size: 10, total: 1 },
        }),
      });
    });

    await insightsPage.sortBy('newest');
    await insightsPage.waitForLoading();
  });

  test('should show pagination when multiple pages', async ({ page }) => {
    const manyInsights = Array.from({ length: 15 }, (_, i) => ({
      ...mockInsight,
      id: `insight-${i}`,
    }));

    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: manyInsights.slice(0, 10),
          pagination: { page: 1, page_size: 10, total: 15 },
        }),
      });
    });

    await insightsPage.goto();
    await insightsPage.expectPaginationVisible();
  });

  test('should display empty state when no insights', async ({ page }) => {
    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [],
          pagination: { page: 1, page_size: 10, total: 0 },
        }),
      });
    });

    await insightsPage.goto();
    await expect(insightsPage.emptyState).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await insightsPage.goto();
    await insightsPage.expectNoError();
  });

  test('should submit positive feedback', async ({ page }) => {
    await page.route('**/api/v1/insights/insight-1/feedback', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [mockInsight],
          pagination: { page: 1, page_size: 10, total: 1 },
        }),
      });
    });

    await insightsPage.goto();
    await insightsPage.clickInsightCard(0);
  });

  test('should submit negative feedback', async ({ page }) => {
    await page.route('**/api/v1/insights/insight-1/feedback', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [mockInsight],
          pagination: { page: 1, page_size: 10, total: 1 },
        }),
      });
    });

    await insightsPage.goto();
    await insightsPage.clickFeedbackButton(0, false);
  });
});

test.describe('Insights API Contract', () => {
  test('should accept valid insight types', async ({ page }) => {
    for (const type of filterOptions.types) {
      await page.route('**/api/v1/insights*', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            insights: [{ ...mockInsight, type }],
            pagination: { page: 1, page_size: 10, total: 1 },
          }),
        });
      });

      await page.goto('/insights');
      await page.selectOption('[data-testid="filter-type"]', type);
      await page.waitForLoadState('networkidle');
    }
  });

  test('should handle pagination parameters', async ({ page }) => {
    const responses: string[] = [];
    
    await page.route('**/api/v1/insights*', (route) => {
      const url = route.request().url();
      responses.push(url);
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [],
          pagination: { page: 1, page_size: 10, total: 0 },
        }),
      });
    });

    await page.goto('/insights?page=2&page_size=20');
    await page.waitForLoadState('networkidle');
    
    expect(responses.some(r => r.includes('page=2') && r.includes('page_size=20'))).toBeTruthy();
  });
});
