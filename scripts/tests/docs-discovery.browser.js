"use strict";
const { test, expect } = require("@playwright/test");

// Registered by docs-browser.spec.js to retain the single isolated server/CI entry.
module.exports = function registerDiscoveryTests({ origin, searchFixture }) {
  for (const channel of ["", "dev/"]) test(`phase3 lazy section search stays in ${channel || "root"} and works by keyboard`, async ({ page }) => {
    const requests = [];
    page.on("request", request => requests.push(new URL(request.url()).pathname));
    await page.goto(`${origin()}/compound-gpid/${channel}#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    expect(requests.filter(url => url.endsWith("search-index.json"))).toEqual([]);
    const trigger = page.getByRole("button", { name: "Search documentation", exact: true });
    await trigger.focus(); await page.keyboard.press("Enter");
    const input = page.locator("[data-search-input]"); await expect(input).toBeFocused();
    await input.fill("Module preferences");
    const first = page.locator(".search-result").first();
    await expect(first).toHaveAttribute("href", "#page=modular-guide&section=module-preferences");
    expect(requests.filter(url => url.endsWith("search-index.json"))).toEqual([`/compound-gpid/${channel}assets/search-index.json`]);
    expect(requests.filter(url => url.endsWith(".md"))).toEqual([`/compound-gpid/${channel}modular-guide.md`]);
    await page.keyboard.press("ArrowDown"); await expect(first).toBeFocused();
    await expect(first).toHaveClass(/selected/);
    await page.keyboard.press("ArrowUp"); await expect(page.locator(".search-result").last()).toBeFocused();
    await page.keyboard.press("ArrowDown"); await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/page=modular-guide&section=module-preferences/);
    await expect(page.locator("[data-search-dialog]")).not.toBeVisible();
    await trigger.focus(); await page.keyboard.press("Enter");
    await input.fill("cg-skill activate");
    await expect(page.locator(".search-result").first()).toHaveAttribute("href", "#page=skill-management-activate");
    await expect(page.locator(".search-result").first()).toContainText("Shared");
    await expect(page.locator('.search-result[href*="page=skill-management-activation"]')).toHaveCount(0);
    await page.keyboard.press("Escape"); await expect(trigger).toBeFocused();
    expect(requests.filter(url => url.endsWith("search-index.json"))).toHaveLength(1);
  });

  test("phase3 Enter activates the focused result after ArrowDown then Tab", async ({ page }) => {
    const markdown = "# Keyboard fixture\n## Keyboard sentinel first\nFirst destination.\n## Keyboard sentinel second\nSecond destination.";
    await page.route("**/modular-guide.md", route => route.fulfill({ body: markdown }));
    await page.route("**/assets/search-index.json", route => route.fulfill({ contentType: "application/json",
      body: searchFixture({ "modular-guide.md": markdown }) }));
    await page.goto(`${origin()}/compound-gpid/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toHaveText(/Keyboard fixture/);
    await page.getByRole("button", { name: "Search documentation", exact: true }).click();
    await page.locator("[data-search-input]").fill("keyboard sentinel");
    const results = page.locator(".search-result"), first = results.nth(0), second = results.nth(1);
    await expect(results).toHaveCount(2);
    await expect(first).toHaveAttribute("href", "#page=modular-guide&section=keyboard-sentinel-first");
    await expect(second).toHaveAttribute("href", "#page=modular-guide&section=keyboard-sentinel-second");
    await page.keyboard.press("ArrowDown"); await expect(first).toBeFocused();
    await expect(first).toHaveClass(/selected/);
    await page.keyboard.press("Tab"); await expect(second).toBeFocused();
    await expect(second).toHaveClass(/selected/); await expect(first).not.toHaveClass(/selected/);
    await page.evaluate(() => document.addEventListener("keydown", event => {
      if (event.key === "Enter" && event.target.closest(".search-result")) window.resultEnterPrevented = event.defaultPrevented;
    }));
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#page=modular-guide&section=keyboard-sentinel-second$/);
    expect(await page.evaluate(() => window.resultEnterPrevented)).toBe(false);
    await expect(page.locator("[data-search-dialog]")).not.toBeVisible();
  });

  for (const completedWhileClosed of [false, true]) test(`phase3 reopen search when index ${completedWhileClosed ? "completed while closed" : "is still pending"}`, async ({ page }) => {
    let release, requests = 0;
    const hold = new Promise(resolve => { release = resolve; });
    await page.route("**/assets/search-index.json", async route => {
      requests += 1; await hold;
      await route.fulfill({ contentType: "application/json", body: searchFixture() });
    });
    await page.goto(`${origin()}/compound-gpid/dev/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    const trigger = page.getByRole("button", { name: "Search documentation", exact: true });
    const input = page.locator("[data-search-input]"), dialog = page.locator("[data-search-dialog]");
    await trigger.click(); await input.fill("Module preferences");
    try {
      await expect.poll(() => requests).toBe(1);
      await expect(page.locator("[data-search-results]")).toContainText("Searching documentation...");
      await page.keyboard.press("Escape"); await expect(dialog).not.toBeVisible();
      await expect(trigger).toBeFocused();
      if (completedWhileClosed) {
        const response = page.waitForResponse("**/assets/search-index.json");
        release(); await (await response).finished();
      }
      await page.keyboard.press("Enter"); await expect(input).toBeFocused();
      await expect(input).toHaveValue("Module preferences");
      release();
      await expect(page.locator(".search-result").first()).toHaveAttribute("href", "#page=modular-guide&section=module-preferences");
      await expect(page.locator("[data-search-results]")).not.toContainText("Searching documentation...");
      expect(requests).toBe(1);
      await page.keyboard.press("Escape"); await expect(trigger).toBeFocused();
      await page.keyboard.press("Enter");
      await expect(page.locator(".search-result").first()).toHaveAttribute("href", "#page=modular-guide&section=module-preferences");
      expect(requests).toBe(1);
    } finally { release(); }
  });

  test("phase3 failed index is retryable and never replaces reading with an incomplete cache", async ({ page }) => {
    let attempts = 0;
    await page.route("**/assets/search-index.json", route => {
      attempts += 1;
      return route.fulfill(attempts === 1 ? { status: 503, body: "unavailable" }
        : { contentType: "application/json", body: searchFixture() });
    });
    await page.goto(`${origin()}/compound-gpid/dev/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    await page.getByRole("button", { name: "Search documentation", exact: true }).click();
    await page.locator("[data-search-input]").fill("Module preferences");
    await expect(page.locator("[data-search-results] [role=alert]")).toContainText("Search unavailable");
    await expect(page.locator(".search-result")).toHaveCount(0);
    await page.getByRole("button", { name: "Retry search", exact: true }).click();
    await expect(page.locator(".search-result").first()).toHaveAttribute("href", "#page=modular-guide&section=module-preferences");
    expect(attempts).toBe(2);
    await page.keyboard.press("Escape");
    await expect(page.locator("[data-document] h1")).toBeVisible();
  });

  test("phase3 malformed index fails closed without executing unsafe destinations", async ({ page }) => {
    const data = JSON.parse(searchFixture()); data.entries[0].url = "javascript:window.injected=true";
    await page.route("**/assets/search-index.json", route => route.fulfill({ contentType: "application/json", body: JSON.stringify(data) }));
    await page.goto(`${origin()}/compound-gpid/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    await page.keyboard.press("ControlOrMeta+k");
    await page.locator("[data-search-input]").fill("Module preferences");
    await expect(page.locator("[data-search-results] [role=alert]")).toContainText("Search unavailable");
    await expect(page.locator(".search-result")).toHaveCount(0);
    expect(await page.evaluate(() => window.injected)).toBeUndefined();
  });

  test("phase3 query races discard stale results and display script-like text safely", async ({ page }) => {
    let release, requested = false;
    const hold = new Promise(resolve => { release = resolve; });
    const markdown = '# Fixture\n## Sentinel <img src=x onerror="window.injected=true">\nSafe data.\n## Other\nRead this.';
    await page.route("**/assets/search-index.json", async route => {
      requested = true; await hold;
      await route.fulfill({ contentType: "application/json", body: searchFixture({ "modular-guide.md": markdown }) });
    });
    await page.goto(`${origin()}/compound-gpid/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    await page.keyboard.press("ControlOrMeta+k");
    const input = page.locator("[data-search-input]"); await input.fill("sentinel");
    try {
      await expect.poll(() => requested).toBe(true);
      await input.fill("no-such-discovery-term");
    } finally { release(); }
    await expect(page.locator("[data-search-results]")).toContainText("No matching documentation");
    await expect(page.locator(".search-result")).toHaveCount(0);
    await input.fill("sentinel");
    await expect(page.locator(".search-result").first()).toContainText('<img src=x onerror="window.injected=true">');
    await expect(page.locator("[data-search-results] img, [data-search-results] script")).toHaveCount(0);
    expect(await page.evaluate(() => window.injected)).toBeUndefined();
  });

  for (const denied of [false, true]) test(`phase3 copy preserves exact bytes with ${denied ? "denied clipboard fallback" : "accessible success"}`, async ({ page }) => {
    const errors = []; page.on("pageerror", error => errors.push(error.message));
    await page.addInitScript(denied => {
      window.copied = [];
      Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async text => {
        if (denied) throw new DOMException("Permission denied", "NotAllowedError");
        window.copied.push(text);
      } } });
    }, denied);
    const code = 'cg-skill inspect "a b"\n  --format json';
    await page.route("**/modular-guide.md", route => route.fulfill({ body: `# Copy fixture\n\n\`\`\`sh\n${code}\n\`\`\`` }));
    await page.goto(`${origin()}/compound-gpid/#page=modular-guide`);
    const button = page.getByRole("button", { name: "Copy code", exact: true });
    await button.focus(); await page.keyboard.press("Enter");
    const status = page.locator("[data-document] [role=status]");
    await expect(status).toContainText(denied ? "Copy failed" : "Copied");
    if (denied) {
      await page.getByRole("button", { name: "Select code", exact: true }).click();
      expect(await page.evaluate(() => getSelection().toString())).toBe(code);
      expect(await page.evaluate(() => window.copied)).toEqual([]);
    } else expect(await page.evaluate(() => window.copied)).toEqual([code]);
    expect(errors).toEqual([]);
  });

  test("phase3 print preserves task commands, suite labels and truthful preview identity", async ({ page }, testInfo) => {
    await page.goto(`${origin()}/compound-gpid/#page=commands`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Task-to-command cheat sheet", exact: true })).toBeVisible();
    await page.emulateMedia({ media: "print" });
    for (const selector of [".topbar", ".sidebar", "[data-toc]", ".copy-code", ".heading-permalink"]) {
      for (const node of await page.locator(selector).all()) await expect(node).toBeHidden();
    }
    await expect(page.locator("[data-build-identity]")).toContainText("Local preview: version unavailable");
    await expect(page.locator("[data-document]")).toContainText("Technical (CG)");
    await expect(page.locator("[data-document]")).toContainText("Research (CR)");
    await expect(page.locator("[data-document]")).toContainText("/cg-work");
    await expect(page.locator("[data-document]")).toContainText("/cr-work");
    await page.screenshot({ path: testInfo.outputPath("commands-print.png"), fullPage: true });
  });

  for (const theme of ["light", "dark"]) test(`phase3 ${theme} drawer, TOC focus and table keyboard journey`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${origin()}/compound-gpid/dev/#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
    const menu = page.getByRole("button", { name: "Open navigation", exact: true });
    await menu.focus(); await page.keyboard.press("Enter");
    for (let i = 0; i < 25; i++) {
      await page.keyboard.press("Tab");
      expect(await page.evaluate(() => Boolean(document.activeElement.closest(".sidebar, [data-menu-close]")))).toBe(true);
    }
    await page.screenshot({ path: testInfo.outputPath(`drawer-${theme}.png`) });
    await page.keyboard.press("Escape"); await expect(menu).toBeFocused();
    await expect.poll(() => page.locator(".sidebar").evaluate(node => node.getBoundingClientRect().right)).toBeLessThanOrEqual(0);
    const summary = page.locator("[data-toc] summary"); await summary.focus(); await page.keyboard.press("Enter");
    const link = page.locator('[data-toc] a[data-section="module-preferences"]');
    await link.focus(); await page.keyboard.press("Enter");
    await expect(page.locator("[data-document] #module-preferences")).toBeFocused();
    await expect(page.locator("[data-document] #module-preferences")).toBeInViewport();
    await page.screenshot({ path: testInfo.outputPath(`toc-focus-${theme}.png`) });
    const table = page.getByRole("region", { name: "Scrollable table" }).first();
    await table.scrollIntoViewIfNeeded();
    await table.focus(); await expect(table).toBeFocused();
    await expect(table).toBeInViewport();
    const before = await table.evaluate(node => ({ left: node.scrollLeft, overflows: node.scrollWidth > node.clientWidth }));
    expect(before.overflows).toBe(true);
    await page.keyboard.press("ArrowRight");
    await expect.poll(() => table.evaluate(node => node.scrollLeft)).toBeGreaterThan(before.left);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`table-scroll-${theme}.png`) });
  });
};
