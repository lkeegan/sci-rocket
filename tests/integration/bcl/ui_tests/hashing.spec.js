const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("hashing tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-hashing"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-hashing")).toBeVisible();
  });

  test("summary table (all cells) has rows", async ({ page }) => {
    await expect(
      page.locator("#sample-hashing-summary-table tbody tr")
    ).not.toHaveCount(0);
  });

  test("summary table (filtered) has rows", async ({ page }) => {
    await expect(
      page.locator("#sample-hashing-summary-filt-table tbody tr")
    ).not.toHaveCount(0);
  });

  test("hashing bins heatmap exists", async ({ page }) => {
    await expect(page.locator("#chart-hashing-bins-heatmap")).toBeAttached();
  });

  test("hashing barcode table has rows", async ({ page }) => {
    await expect(
      page.locator("#sample-hashing-table tbody tr")
    ).not.toHaveCount(0);
  });
});
