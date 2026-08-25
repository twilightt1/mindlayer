import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

export class WorkspacesPage extends BasePage {
  readonly header: Locator;
  readonly workspaceList: Locator;
  readonly createButton: Locator;
  readonly inviteModal: Locator;
  readonly memberList: Locator;
  readonly addMemberButton: Locator;
  readonly settingsButton: Locator;
  readonly deleteButton: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.locator('h1:has-text("Workspaces")');
    this.workspaceList = page.locator('[data-testid="workspace-list"], [class*="workspace"]');
    this.createButton = page.locator('button:has-text("Create"), button:has-text("New")');
    this.inviteModal = page.locator('[data-testid="invite-modal"], [role="dialog"]');
    this.memberList = page.locator('[data-testid="member-list"]');
    this.addMemberButton = page.locator('button:has-text("Add Member"), button:has-text("Invite")');
    this.settingsButton = page.locator('button:has-text("Settings")');
    this.deleteButton = page.locator('button:has-text("Delete"), button:has-text("Remove")');
  }

  async goto() {
    await this.page.goto('/workspaces');
    await this.page.waitForLoadState('networkidle');
  }

  async clickCreateWorkspace() {
    await this.createButton.click();
  }

  async clickWorkspace(index: number = 0) {
    await this.workspaceList.nth(index).click();
  }

  async openInviteModal() {
    await this.addMemberButton.click();
    await expect(this.inviteModal).toBeVisible();
  }

  async closeInviteModal() {
    await this.page.keyboard.press('Escape');
    await expect(this.inviteModal).not.toBeVisible();
  }

  async expectWorkspaceCount(count: number) {
    await expect(this.workspaceList.locator('[data-testid="workspace-item"]')).toHaveCount(count);
  }

  async expectMemberListVisible() {
    await expect(this.memberList).toBeVisible();
  }

  async removeMember(index: number = 0) {
    const memberItem = this.memberList.locator('[data-testid="member-item"]').nth(index);
    await memberItem.hover();
    await memberItem.locator('button').last().click();
  }
}
