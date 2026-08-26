import { test as setup, expect } from '@playwright/test';

/**
 * Global setup for E2E tests
 * This runs once before all tests
 */
setup('global setup', async ({ page }) => {
  // Navigate to the app
  await page.goto('/');
  
  // Wait for app to be ready
  await page.waitForLoadState('networkidle');
  
  // Check if we're on the right page
  await expect(page).toHaveTitle(/Orivory/i);
  
  // For authenticated pages, you would:
  // 1. Check if user is logged in
  // 2. If not, perform login
  // 3. Store auth state for subsequent tests
});
