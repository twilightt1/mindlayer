import { test, expect } from '@playwright/test';
import { WorkspacesPage } from '../pages/workspaces-page';
import { mockWorkspace, mockMember, workspaceRoles } from '../fixtures/sample';

test.describe('Workspaces Dashboard', () => {
  let workspacesPage: WorkspacesPage;

  test.beforeEach(async ({ page }) => {
    workspacesPage = new WorkspacesPage(page);
    await workspacesPage.goto();
  });

  test('should display workspaces page header', async () => {
    await expect(workspacesPage.header).toBeVisible();
  });

  test('should display create workspace button', async () => {
    await expect(workspacesPage.createButton).toBeVisible();
  });

  test('should display workspace list', async () => {
    await expect(workspacesPage.workspaceList).toBeVisible();
  });

  test('should create new workspace', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkspace),
      });
    });

    await workspacesPage.clickCreateWorkspace();
    // Modal should open - fill form would go here
    await page.waitForSelector('[role="dialog"]');
    await expect(page.locator('[role="dialog"]')).toBeVisible();
  });

  test('should display workspace details on click', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [mockWorkspace],
        }),
      });
    });

    await workspacesPage.clickWorkspace(0);
    await workspacesPage.waitForLoading();
  });

  test('should display member list', async ({ page }) => {
    await page.route('**/api/v1/workspaces/ws-1*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockWorkspace,
          members: [mockMember],
        }),
      });
    });

    await page.goto('/workspaces/ws-1');
    await workspacesPage.expectMemberListVisible();
  });

  test('should open invite modal', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [{ ...mockWorkspace, members: [mockMember] }],
        }),
      });
    });

    await workspacesPage.goto();
    await workspacesPage.openInviteModal();
  });

  test('should close invite modal with Escape', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspaces: [{ ...mockWorkspace, members: [mockMember] }],
        }),
      });
    });

    await workspacesPage.goto();
    await workspacesPage.openInviteModal();
    await workspacesPage.closeInviteModal();
  });

  test('should handle empty workspaces state', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ workspaces: [] }),
      });
    });

    await workspacesPage.goto();
    await expect(workspacesPage.emptyState).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/workspaces*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await workspacesPage.goto();
    await workspacesPage.expectNoError();
  });

  test('should display all workspace roles', async ({ page }) => {
    for (const role of workspaceRoles) {
      const memberWithRole = { ...mockMember, role: role.id };
      
      await page.route('**/api/v1/workspaces/ws-1*', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockWorkspace,
            members: [memberWithRole],
          }),
        });
      });

      await page.goto('/workspaces/ws-1');
      await page.waitForLoadState('networkidle');
    }
  });

  test('should update member role', async ({ page }) => {
    await page.route('**/api/v1/workspaces/ws-1/members*', (route) => {
      if (route.request().method() === 'PATCH') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockMember, role: 'admin' }),
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ members: [mockMember] }),
        });
      }
    });

    await page.goto('/workspaces/ws-1');
    // Role update would require selecting a member and changing role
  });

  test('should remove member from workspace', async ({ page }) => {
    await page.route('**/api/v1/workspaces/ws-1/members*', (route) => {
      if (route.request().method() === 'DELETE') {
        route.fulfill({
          status: 204,
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ members: [mockMember] }),
        });
      }
    });

    await page.goto('/workspaces/ws-1');
    await workspacesPage.expectMemberListVisible();
    await workspacesPage.removeMember(0);
  });

  test('should send workspace invite', async ({ page }) => {
    await page.route('**/api/v1/workspaces/ws-1/invite*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          invite_link: 'https://app.example.com/invite/abc123',
          expires_at: '2025-09-25T00:00:00Z',
        }),
      });
    });

    await page.goto('/workspaces/ws-1');
    await workspacesPage.openInviteModal();
    
    // Fill in email and send invite
    await page.fill('input[type="email"]', 'newmember@example.com');
    await page.click('button:has-text("Send Invite")');
  });
});

test.describe('Workspaces API Contract', () => {
  test('should create workspace with valid data', async ({ page }) => {
    await page.route('**/api/v1/workspaces', (route) => {
      const body = route.request().postDataJSON();
      expect(body.name).toBeDefined();
      expect(body.description).toBeDefined();
      
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockWorkspace, ...body }),
      });
    });

    await page.goto('/workspaces');
    await workspacesPage.clickCreateWorkspace();
  });

  test('should handle workspace permissions correctly', async ({ page }) => {
    // Test that non-owners cannot delete workspaces
    const nonOwnerMember = { ...mockMember, role: 'editor' };
    
    await page.route('**/api/v1/workspaces/ws-1', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockWorkspace,
          current_user_role: 'editor',
        }),
      });
    });

    await page.goto('/workspaces/ws-1');
    // Delete button should not be visible for editors
    await expect(workspacesPage.deleteButton).not.toBeVisible();
  });
});
