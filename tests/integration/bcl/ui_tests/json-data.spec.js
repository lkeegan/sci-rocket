const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("sci-dash data (JSON) tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-data"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-data")).toBeVisible();
  });

  test("JSON data is present and valid", async ({ page }) => {
    const text = await page.locator("#json-data").textContent();
    expect(text.length).toBeGreaterThan(0);
    const parsed = JSON.parse(text);
    expect(parsed).toHaveProperty("experiment_name");
    expect(parsed).toHaveProperty("n_pairs");
    expect(parsed).toHaveProperty("sample_success");
  });
});
