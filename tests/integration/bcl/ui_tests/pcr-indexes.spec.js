const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("counts - PCR indexes tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-pcr"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-pcr")).toBeVisible();
  });

  test("p5 index chart canvas exists", async ({ page }) => {
    await expect(page.locator("#chart-well-p5")).toBeAttached();
  });

  test("p7 index chart canvas exists", async ({ page }) => {
    await expect(page.locator("#chart-well-p7")).toBeAttached();
  });

  test("ligation bar chart canvas exists", async ({ page }) => {
    await expect(page.locator("#chart-ligation")).toBeAttached();
  });
});
