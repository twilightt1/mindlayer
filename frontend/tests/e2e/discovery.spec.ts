import { test, expect } from '@playwright/test';
import { DiscoveryPage } from '../pages/discovery-page';
import { mockDiscoveryFlow, flowTypes } from '../fixtures/sample';

test.describe('Discovery Dashboard', () => {
  let discoveryPage: DiscoveryPage;

  test.beforeEach(async ({ page }) => {
    discoveryPage = new DiscoveryPage(page);
    await discoveryPage.goto();
  });

  test('should display discovery page header', async () => {
    await expect(discoveryPage.header).toBeVisible();
  });

  test('should display flow type selector', async () => {
    await expect(discoveryPage.flowTypeSelector).toBeVisible();
  });

  test('should display bento grid layout', async () => {
    await expect(discoveryPage.bentoGrid).toBeVisible();
  });

  test('should display timeline component', async () => {
    await expect(discoveryPage.timeline).toBeVisible();
  });

  test('should display flow cards', async () => {
    await expect(discoveryPage.flowCards.first()).toBeVisible();
  });

  test('should display start flow button', async () => {
    await expect(discoveryPage.startFlowButton).toBeVisible();
  });

  test('should select flow type', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          flows: [{ ...mockDiscoveryFlow, flow_type: 'related_docs' }],
        }),
      });
    });

    await discoveryPage.selectFlowType('related_docs');
    await discoveryPage.waitForLoading();
    await expect(discoveryPage.flowCards.first()).toBeVisible();
  });

  test('should display all 5 flow types', async ({ page }) => {
    const allFlows = flowTypes.map((f, i) => ({
      ...mockDiscoveryFlow,
      id: `flow-${i}`,
      flow_type: f.id,
    }));

    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: allFlows }),
      });
    });

    await discoveryPage.goto();
    await discoveryPage.expectFlowCount(5);
  });

  test('should handle empty flows state', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [] }),
      });
    });

    await discoveryPage.goto();
    await expect(discoveryPage.emptyState).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await discoveryPage.goto();
    await discoveryPage.expectNoError();
  });

  test('should start discovery flow on card click', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [mockDiscoveryFlow] }),
      });
    });

    await discoveryPage.clickFlowCard(0);
    await discoveryPage.waitForLoading();
  });

  test('should start discovery flow on button click', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [mockDiscoveryFlow] }),
      });
    });

    await discoveryPage.startDiscoveryFlow();
    await discoveryPage.waitForLoading();
  });

  test('should show timeline with multiple steps', async ({ page }) => {
    const multiStepFlow = {
      ...mockDiscoveryFlow,
      steps: [
        { id: 'step-1', query: 'First query', documents: ['doc-1'], answer: 'Answer 1' },
        { id: 'step-2', query: 'Second query', documents: ['doc-2'], answer: 'Answer 2' },
        { id: 'step-3', query: 'Third query', documents: ['doc-3'], answer: 'Answer 3' },
      ],
    };

    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [multiStepFlow] }),
      });
    });

    await discoveryPage.goto();
    await discoveryPage.expectTimelineVisible();
  });
});

test.describe('Discovery API Contract', () => {
  test('should accept all flow types', async ({ page }) => {
    for (const flowType of flowTypes) {
      await page.route('**/api/v1/discovery/flows*', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            flows: [{ ...mockDiscoveryFlow, flow_type: flowType.id }],
          }),
        });
      });

      await page.goto('/discovery');
      await page.selectOption('[data-testid="flow-type"]', flowType.id);
      await page.waitForLoadState('networkidle');
    }
  });

  test('should handle discovery metrics endpoint', async ({ page }) => {
    await page.route('**/api/v1/discovery/metrics*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_flows: 42,
          avg_completion_rate: 0.85,
          avg_steps_per_flow: 3.2,
        }),
      });
    });

    await page.goto('/discovery');
    await page.waitForLoadState('networkidle');
  });
});
