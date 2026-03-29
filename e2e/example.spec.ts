import { test, expect } from '@playwright/test'

test('页面加载测试', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/Yumi/)
})
