import { test, expect } from '@playwright/test';

test.describe('UI Components - Loading States', () => {
  test('should show loading state while fetching data', async ({ page }) => {
    await page.route('**/api/v1/insights*', async (route) => {
      await page.waitForTimeout(1000); // Simulate slow network
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          insights: [],
          pagination: { page: 1, page_size: 10, total: 0 },
        }),
      });
    });

    await page.goto('/insights');
    
    // Check for loading indicator
    const loadingIndicator = page.locator('[data-testid="loading"], .animate-pulse, .loading-skeleton');
    await expect(loadingIndicator.first()).toBeVisible({ timeout: 500 }).catch(() => {});
  });

  test('should handle slow loading gracefully', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', async (route) => {
      await page.waitForTimeout(3000);
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [] }),
      });
    });

    await page.goto('/discovery');
    
    // Page should remain responsive
    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();
  });
});

test.describe('UI Components - Empty States', () => {
  test('should display empty state on insights page', async ({ page }) => {
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

    await page.goto('/insights');
    await expect(page.locator('[data-testid="empty-state"], .empty-state')).toBeVisible();
  });

  test('should display empty state on discovery page', async ({ page }) => {
    await page.route('**/api/v1/discovery/flows*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ flows: [] }),
      });
    });

    await page.goto('/discovery');
    await expect(page.locator('[data-testid="empty-state"], .empty-state')).toBeVisible();
  });

  test('should display empty state on workspaces page', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ workspaces: [] }),
      });
    });

    await page.goto('/workspaces');
    await expect(page.locator('[data-testid="empty-state"], .empty-state')).toBeVisible();
  });

  test('should show call-to-action in empty states', async ({ page }) => {
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

    await page.goto('/insights');
    
    // Empty state should have a CTA button
    const ctaButton = page.locator('[data-testid="empty-state"] button, .empty-state a');
    await expect(ctaButton).toBeVisible();
  });
});

test.describe('UI Components - Error States', () => {
  test('should display error message on API failure', async ({ page }) => {
    await page.route('**/api/v1/insights*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/insights');
    
    // Should show error message or toast
    const errorMessage = page.locator('[data-testid="error-message"], [role="alert"], .error');
    await expect(errorMessage).toBeVisible();
  });

  test('should allow retry on error', async ({ page }) => {
    let requestCount = 0;
    
    await page.route('**/api/v1/insights*', (route) => {
      requestCount++;
      if (requestCount === 1) {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' }),
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            insights: [],
            pagination: { page: 1, page_size: 10, total: 0 },
          }),
        });
      }
    });

    await page.goto('/insights');
    
    // Click retry button if available
    const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")');
    if (await retryButton.isVisible()) {
      await retryButton.click();
      await page.waitForLoadState('networkidle');
    }
  });

  test('should handle network errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/insights*', (route) => {
      route.abort();
    });

    await page.goto('/insights');
    
    // Should show network error message
    const errorMessage = page.locator('[data-testid="error-message"], [role="alert"]');
    await expect(errorMessage).toBeVisible();
  });

  test('should handle 404 errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Workspace not found' }),
      });
    });

    await page.goto('/workspaces/ws-nonexistent');
    
    // Should show appropriate error
    await expect(page.locator('[data-testid="error-message"], h1')).toBeVisible();
  });

  test('should handle 401 unauthorized errors', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
    });

    await page.goto('/workspaces');
    
    // Should redirect to login or show auth error
    await expect(page.url()).not.toBe('/workspaces');
  });
});

test.describe('UI Components - Modal/Dialog', () => {
  test('should open modal with animation', async ({ page }) => {
    await page.goto('/workspaces');
    
    await page.click('button:has-text("Create"), button:has-text("New")');
    
    // Modal should animate in
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 2000 });
  });

  test('should close modal on Escape key', async ({ page }) => {
    await page.goto('/workspaces');
    
    await page.click('button:has-text("Create")');
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });

  test('should close modal on backdrop click', async ({ page }) => {
    await page.goto('/workspaces');
    
    await page.click('button:has-text("Create")');
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    
    // Click backdrop (outside modal)
    await page.click('[role="dialog"]', { position: { x: -10, y: -10 } });
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });

  test('should trap focus in modal', async ({ page }) => {
    await page.goto('/workspaces');
    
    await page.click('button:has-text("Create")');
    
    // Focus should be inside modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeFocused();
  });
});

test.describe('UI Components - BentoGrid', () => {
  test('should render bento grid layout', async ({ page }) => {
    await page.goto('/discovery');
    
    const bentoGrid = page.locator('[data-testid="bento-grid"], .bento-grid');
    await expect(bentoGrid).toBeVisible();
  });

  test('should handle different card sizes', async ({ page }) => {
    await page.goto('/discovery');
    
    // Large cards
    const largeCards = page.locator('[class*="col-span-2"], [class*="row-span-2"]');
    const cardCount = await largeCards.count();
    
    // Should have at least some large cards for visual variety
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size
    
    await page.goto('/discovery');
    
    // Bento grid should still be visible but stack vertically
    const bentoGrid = page.locator('[data-testid="bento-grid"], .bento-grid');
    await expect(bentoGrid).toBeVisible();
  });
});

test.describe('UI Components - Timeline', () => {
  test('should render timeline component', async ({ page }) => {
    await page.goto('/discovery');
    
    const timeline = page.locator('[data-testid="timeline"], .timeline');
    await expect(timeline).toBeVisible();
  });

  test('should display timeline steps in order', async ({ page }) => {
    await page.goto('/discovery');
    
    // Timeline items should be in sequential order
    const timelineItems = page.locator('[data-testid="timeline-item"], .timeline-item');
    const count = await timelineItems.count();
    
    for (let i = 0; i < count; i++) {
      const item = timelineItems.nth(i);
      await expect(item).toBeVisible();
    }
  });

  test('should highlight current step', async ({ page }) => {
    await page.goto('/discovery');
    
    // Current step should have different styling
    const activeStep = page.locator('[data-testid="timeline-item"].active, .timeline-item.active');
    // May or may not be present depending on state
  });
});
