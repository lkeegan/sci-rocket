const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("sci-dash smoke tests", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  let errors;

  test.beforeEach(async ({ page }) => {
    errors = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto(`file://${dashboardPath}`);
  });

  test("no JavaScript errors on page load", async () => {
    expect(errors).toEqual([]);
  });

  test("experiment name renders", async ({ page }) => {
    await expect(page.locator("#experiment_name")).not.toHaveText("N/A");
  });

  test("total read pairs renders", async ({ page }) => {
    await expect(page.locator("#n_total_pairs")).not.toHaveText("N/A");
  });

  test("STARSolo table has rows", async ({ page }) => {
    await expect(
      page.locator("#sample-starsolo-table tbody tr")
    ).not.toHaveCount(0);
  });
});
