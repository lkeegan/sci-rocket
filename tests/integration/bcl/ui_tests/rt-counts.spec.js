const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("counts - RT tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
    await page.locator('a[href="#tabs-rt"]').click();
  });

  test("tab content is visible", async ({ page }) => {
    await expect(page.locator("#tabs-rt")).toBeVisible();
  });

  test("at least one RT plate chart exists", async ({ page }) => {
    const plate1 = page.locator("#chart-rt_plate_01");
    const plate2 = page.locator("#chart-rt_plate_02");
    const plate3 = page.locator("#chart-rt_plate_03");
    const plate4 = page.locator("#chart-rt_plate_04");
    const count =
      (await plate1.count()) +
      (await plate2.count()) +
      (await plate3.count()) +
      (await plate4.count());
    expect(count).toBeGreaterThan(0);
  });
});
