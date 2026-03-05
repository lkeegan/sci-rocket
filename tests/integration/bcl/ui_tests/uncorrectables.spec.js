const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("uncorrectable barcodes tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-uncorrectables"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-uncorrectables")).toBeVisible();
  });

  test("sankey diagram exists", async ({ page }) => {
    await expect(page.locator("#chart-sankey")).toBeAttached();
  });

  test("ligation uncorrectables chart exists", async ({ page }) => {
    await expect(page.locator("#chart-top_uncorrectables_lig")).toBeAttached();
  });

  test("RT uncorrectables chart exists", async ({ page }) => {
    await expect(page.locator("#chart-top_uncorrectables_rt")).toBeAttached();
  });

  test("copy buttons are present", async ({ page }) => {
    await expect(
      page.locator('button.copy-btn[data-type="ligation"]')
    ).toBeAttached();
    await expect(
      page.locator('button.copy-btn[data-type="rt"]')
    ).toBeAttached();
  });
});
