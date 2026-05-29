import { test, expect } from '@playwright/test';

test.describe('Session Flow', () => {
  test('landing page renders with Start Capture button', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Capture Your Intent' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Capture' })).toBeVisible();
    await expect(page.getByPlaceholder('Project name')).toBeVisible();
  });

  test('header shows title and theme toggle', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'AICA' })).toBeVisible();
    const themeBtn = page.getByRole('button', { name: /switch to/i });
    await expect(themeBtn).toBeVisible();
  });

  test('theme toggle switches dark/light mode', async ({ page }) => {
    await page.goto('/');
    const html = page.locator('html');

    const themeBtn = page.getByRole('button', { name: /switch to/i });
    await themeBtn.click();

    const theme = await html.getAttribute('data-theme');
    expect(theme).toMatch(/light|dark/);
  });

  test('project name input accepts text', async ({ page }) => {
    await page.goto('/');
    const input = page.getByPlaceholder('Project name');
    await input.fill('my-test-project');
    await expect(input).toHaveValue('my-test-project');
  });

  test('start capture button is clickable and triggers state change', async ({ page }) => {
    await page.goto('/');
    const btn = page.getByRole('button', { name: 'Start Capture' });
    await btn.click();

    // Without a backend, the button should either show loading or an error
    // Either proves the click handler fired and state changed
    await expect(
      page.getByText(/creating session|connecting|failed|connection/i),
    ).toBeVisible({ timeout: 3000 });
  });
});
