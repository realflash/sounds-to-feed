import { test, expect } from '@playwright/test';

test('baseline system verification', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/PRODUCT_NAME/);
});
