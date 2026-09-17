"use strict";
const { test, expect } = require("@playwright/test");
const fs = require("node:fs"), path = require("node:path");
module.exports = function commandCases(origin) {
  test("command display text stays inert and invalid links reject the whole index", async ({ page }) => {
    const value = JSON.parse(fs.readFileSync(path.join(__dirname, "../../docs/assets/command-index.json")));
    value.commands[0].summary = '<img src=x onerror="window.commandInjected=true"> [run](javascript:alert(1))';
    await page.route("**/command-index.json", route => route.fulfill({ json: value }));
    const markdown = fs.readFileSync(path.join(__dirname, "../../docs/reference/commands.md"), "utf8") +
      '\n## Entity safety\n\n| Text |\n| --- |\n| &lt;img src=x onerror=&quot;window.tableInjected=true&quot;&gt; &#91;run&#93;&#40;javascript:alert&#40;1&#41;&#41; |\n';
    await page.route("**/reference/commands.md", route => route.fulfill({ body: markdown }));
    await page.goto(`${origin()}/compound-gpid/#page=commands`);
    const first = page.locator(".command-card").first(); await first.locator("summary").click();
    await expect(first).toContainText(value.commands[0].summary);
    await expect(first.locator("img, script, a[href^='javascript:']")).toHaveCount(0);
    expect(await page.evaluate(() => window.commandInjected)).toBeUndefined();
    await expect(page.locator("[data-document] table").filter({ hasText: "window.tableInjected" })).toContainText('<img src=x onerror="window.tableInjected=true"> [run](javascript:alert(1))');
    await expect(page.locator("[data-document] table img, [data-document] table a[href^='javascript:']")).toHaveCount(0);
    expect(await page.evaluate(() => window.tableInjected)).toBeUndefined();
    await expect(page.locator("[data-document] td").filter({ hasText: /^\/cg-work \[phaseX\] \[review\]/ }).first()).toBeVisible();
    value.commands[0].route.page = "javascript:alert(1)";
    await page.reload();
    await expect(page.locator(".command-browser [role=status]")).toContainText("unavailable");
    await expect(page.locator(".command-card")).toHaveCount(0);
    value.commands[0].route.page = "commands";
    await page.getByRole("button", { name: "Retry command catalog", exact: true }).click();
    await expect(page.locator(".command-card")).toHaveCount(57);
  });

  test("command filters and expanded facts fit a narrow dark screen and pass accessibility checks", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto(`${origin()}/compound-gpid/dev/#page=commands`);
    await expect(page.locator(".command-card")).toHaveCount(57);
    await page.evaluate(() => document.documentElement.dataset.theme = "dark");
    await page.locator('[data-command-filter="kind"]').selectOption("shell");
    await page.locator(".command-card summary").first().click();
    await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
    const results = await page.evaluate(() => axe.run(".command-browser", { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] } }));
    expect(results.violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
};
