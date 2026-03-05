const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("overview", () => {
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

  test("version renders", async ({ page }) => {
    await expect(page.locator("#version")).not.toBeEmpty();
  });

  test("experiment name renders", async ({ page }) => {
    await expect(page.locator("#experiment_name")).not.toHaveText("N/A");
  });

  test("total read pairs renders", async ({ page }) => {
    await expect(page.locator("#n_total_pairs")).not.toHaveText("N/A");
  });

  test("success percentage renders", async ({ page }) => {
    await expect(page.locator("#n_total_pairs_success_perc")).not.toBeEmpty();
  });

  test("failure percentage renders", async ({ page }) => {
    await expect(page.locator("#n_total_pairs_failure_perc")).not.toBeEmpty();
  });

  test("success progress bar has width", async ({ page }) => {
    const bar = page.locator("#n_total_pairs_success_perc_bar");
    const width = await bar.evaluate((el) => el.style.width);
    expect(width).not.toBe("");
    expect(width).not.toBe("0%");
  });

  test("total corrections renders", async ({ page }) => {
    await expect(page.locator("#n_total_corrections")).not.toBeEmpty();
  });

  test("corrections pie chart canvas exists", async ({ page }) => {
    await expect(page.locator("#chart-rescues")).toBeAttached();
  });

  test("total samples renders", async ({ page }) => {
    await expect(page.locator("#n_totalsamples")).not.toBeEmpty();
  });

  test("total cells renders", async ({ page }) => {
    await expect(page.locator("#n_total_cells")).not.toBeEmpty();
  });

  test("pairs per sample bar chart canvas exists", async ({ page }) => {
    await expect(page.locator("#chart-n_pairs_sample")).toBeAttached();
  });
});
