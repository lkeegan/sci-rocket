const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("benchmarks tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-benchmarks"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-benchmarks")).toBeVisible();
  });

  test("table has rows", async ({ page }) => {
    await expect(
      page.locator("#benchmarks-table tbody tr")
    ).not.toHaveCount(0);
  });

  test("table has expected column headers", async ({ page }) => {
    const headers = page.locator("#benchmarks-table thead th");
    const texts = await headers.allTextContents();
    expect(texts).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Job"),
        expect.stringContaining("Time"),
        expect.stringContaining("Max RAM"),
      ])
    );
  });
});
