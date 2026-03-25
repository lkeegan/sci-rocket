const { test, expect } = require("@playwright/test");
const { dashboardPath, hasDashboard } = require("./dashboard-path");


test.describe("alignment (STARSolo) tab", () => {
  test.skip(!hasDashboard, "sci-dash output not found");

  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${dashboardPath}`);
  });

  test("tab is active by default", async ({ page }) => {
    await expect(page.locator('#tabs-starsolo')).toBeVisible();
  });

  test("table has rows", async ({ page }) => {
    await expect(
      page.locator("#sample-starsolo-table tbody tr")
    ).not.toHaveCount(0);
  });

  test("table has expected column headers", async ({ page }) => {
    const headers = page.locator("#sample-starsolo-table thead th");
    const texts = await headers.allTextContents();
    expect(texts).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Sample"),
        expect.stringContaining("Sequencing saturation"),
        expect.stringContaining("Estimated cells"),
      ])
    );
  });

  test("sequencing saturation values are present", async ({ page }) => {
    const cells = page.locator("#sample-starsolo-table tbody tr td:nth-child(3)");
    const count = await cells.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      await expect(cells.nth(i)).not.toBeEmpty();
    }
  });

  test("estimated cells values are present", async ({ page }) => {
    const rows = page.locator("#sample-starsolo-table tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const lastCell = rows.nth(i).locator("td:last-child");
      await expect(lastCell).not.toBeEmpty();
    }
  });

  test("preliminary umap controls and cards render", async ({ page }) => {
    await expect(page.locator("#umap-color-select")).toBeVisible();
    await expect(page.locator("#sample-umap-grid .card")).not.toHaveCount(0);
    const plot = page.locator("#sample-umap-grid .sample-umap-plot").first();
    await expect(plot).toBeVisible();
    await expect(plot.locator(".svg-container, canvas")).not.toHaveCount(0);
  });
});
