"use strict";
const { test, expect } = require("@playwright/test");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const docs = path.resolve(__dirname, "../../docs");
let server, origin;

// Each run owns an ephemeral loopback port; it cannot reuse a developer server.
test.beforeAll(async () => {
  server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://localhost");
    const match = /^\/compound-gpid\/(dev\/)?(.*)$/.exec(url.pathname);
    const relative = match && (match[2] || "index.html");
    if (!relative || relative.split("/").some(part => part === "..") || /%|\\/.test(relative)) {
      response.writeHead(404).end(); return;
    }
    const file = path.join(docs, relative);
    try {
      let bytes = fs.readFileSync(file);
      if (match[1] && relative === "index.html") bytes = Buffer.from(bytes.toString().replace("<body>",
        '<body><div class="dev-preview-banner">Development preview. Content can change before release.</div>'));
      const type = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" }[path.extname(file)] || "text/plain";
      response.writeHead(200, { "Content-Type": `${type}; charset=utf-8`, "Cache-Control": "no-store" }).end(bytes);
    } catch { response.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
});
test.afterAll(async () => { await new Promise(resolve => server.close(resolve)); });
test.beforeEach(async ({ page }) => {
  await page.route(/fonts\.(googleapis|gstatic)\.com/, route => route.abort());
});

test("seven collapsible groups and a separate right TOC", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${origin}/compound-gpid/#page=modular-guide`);
  const groups = page.locator("[data-nav-group]");
  await expect(groups).toHaveCount(7);
  const active = page.getByRole("button", { name: "Start Here", exact: true });
  await expect(active).toHaveAttribute("aria-expanded", "true");
  await active.click(); await expect(active).toHaveAttribute("aria-expanded", "false");
  await active.click();
  const toc = page.getByRole("navigation", { name: "On this page", exact: true });
  await expect(toc).toBeVisible();
  const articleBox = await page.locator("[data-document]").boundingBox();
  const tocBox = await toc.boundingBox();
  expect(tocBox.x).toBeGreaterThan(articleBox.x + articleBox.width - 1);
  await expect(page.getByRole("navigation", { name: "Breadcrumb" })).toContainText("Start Here");
  await expect(page.locator("[data-navigation]")).not.toContainText("`cg-skill");
});

test("section movement, skip link and history do not fetch or replace the article", async ({ page }) => {
  let fetched = 0;
  page.on("request", request => { if (request.url().endsWith("modular-guide.md")) fetched += 1; });
  await page.goto(`${origin}/compound-gpid/#page=modular-guide&section=module-preferences`);
  await expect(page.locator("[data-document] #module-preferences")).toBeVisible();
  await page.evaluate(() => { document.querySelector("[data-document]").dataset.retained = "yes"; });
  const toc = page.getByRole("navigation", { name: "On this page", exact: true });
  await toc.getByRole("link", { name: "How suites compose capabilities", exact: true }).click();
  await expect(page).toHaveURL(/section=how-suites-compose-capabilities/);
  await expect(page.locator("[data-document]")).toHaveAttribute("data-retained", "yes");
  await page.goBack(); await expect(page).toHaveURL(/section=module-preferences/);
  await page.goForward(); await expect(page).toHaveURL(/section=how-suites-compose-capabilities/);
  const before = page.url();
  await page.locator(".skip-link").focus(); await page.keyboard.press("Enter");
  await expect(page.locator("#content")).toBeFocused();
  expect(page.url()).toBe(before); expect(fetched).toBe(1);
});

test("route races, unknown routes, missing sections and failed loads clear stale TOCs", async ({ page }) => {
  await page.route("**/modular-guide.md", async route => {
    await new Promise(resolve => setTimeout(resolve, 250)); await route.continue();
  });
  await page.goto(`${origin}/compound-gpid/#page=modular-guide`);
  await page.evaluate(() => { location.hash = "page=research"; });
  await expect(page.locator("[data-document] h1")).toContainText("Research");
  await page.waitForTimeout(350);
  await expect(page.locator("[data-document] h1")).toContainText("Research");
  await page.evaluate(() => { location.hash = "page=research&section=absent"; });
  await expect(page.locator("[data-route-notice]")).toContainText("not available");
  await page.evaluate(() => { location.hash = "page=absent"; });
  await expect(page.locator("[data-document] h1")).toHaveText("Page not found");
  await expect(page.locator("[data-toc]")).toBeHidden();
  await page.route("**/modular-guide.md", route => route.fulfill({ status: 503, body: "unavailable" }));
  await page.evaluate(() => { location.hash = "page=modular-guide"; });
  await expect(page.locator("[data-document] h1")).toHaveText("Page unavailable");
  await expect(page.locator("[data-toc]")).toBeHidden();
  await page.evaluate(() => { location.hash = "home"; });
  await expect(page.locator("[data-toc]")).toBeHidden();
});

test("storage failure keeps reading, theme selection and mobile focus usable", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new Error("Storage denied"); } });
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${origin}/compound-gpid/dev/#page=modular-guide`);
  await expect(page.locator("[data-document] h1")).toBeVisible();
  await page.getByRole("button", { name: "Switch color theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Open navigation", exact: true }).click();
  await expect(page.locator(".sidebar")).toHaveClass(/open/);
  await expect(page.locator(".sidebar [data-toc]")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Open navigation", exact: true })).toBeFocused();
  await page.getByText("On this page", { exact: true }).click();
  await expect(page.getByRole("navigation", { name: "On this page", exact: true })).toBeVisible();
});

for (const width of [320, 390, 768, 1024, 1440]) {
  for (const channel of ["", "dev/"]) test(`responsive accessible ${channel || "root"} at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(`${origin}/compound-gpid/${channel}#page=modular-guide`);
    await expect(page.locator("[data-document] h1")).toBeVisible();
    for (const theme of ["light", "dark"]) {
      await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
      const violations = await page.evaluate(async () => (await axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] } })).violations);
      expect(violations.map(v => `${v.id}: ${v.nodes.map(n => n.target).join(", ")}`)).toEqual([]);
    }
    await page.screenshot({ path: testInfo.outputPath(`shell-${width}.png`), fullPage: false });
  });
}

test("200 percent zoom reflows and no-JavaScript fallback stays useful", async ({ page, browser }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${origin}/compound-gpid/dev/#page=modular-guide&section=module-preferences`);
  await expect(page.locator("[data-document] h1")).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.zoom = "2"; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const context = await browser.newContext({ javaScriptEnabled: false });
  const plain = await context.newPage(); await plain.goto(`${origin}/compound-gpid/`);
  await expect(plain.locator("noscript a")).toHaveCount(2);
  await expect(plain.locator("noscript")).toBeVisible(); await context.close();
});

test("every old narrative route maps to the unified guide while raw Markdown stays useful", async ({ page, request }) => {
  test.setTimeout(60000);
  const manifest = JSON.parse(fs.readFileSync(path.join(docs, "navigation.json")));
  for (const config of manifest.groups.flatMap(group => group.pages).filter(config => config.redirect)) {
    const entries = Object.entries(config.redirect.sections);
    const [old, section] = entries.at(-1);
    await page.goto(`${origin}/compound-gpid/dev/#page=${config.id}&section=${old}`);
    await expect(page.locator("[data-document] h1")).toContainText("Skill Management");
    await expect(page.locator(`[data-document] [id="${section}"]`)).toBeVisible();
    await expect(page.locator("[data-route-notice]")).toHaveCount(0);
    const markdown = await request.get(`${origin}/compound-gpid/${config.file}`);
    expect(markdown.ok()).toBe(true); expect(await markdown.text()).toMatch(/\]\([^)]*index\.md#/);
  }
});

test("duplicate headings, safe callouts, keyboard TOC focus and banner offsets", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route("**/modular-guide.md", route => route.fulfill({ body:
    "# Fixture\n## First\nText.\n## Repeat\nText.\n## Repeat\n> [!WARNING] <script>window.injected=true</script>\n## Caf\u00e9 `API()`\n```md\n## Not a heading\n```\n" + "\nLong text.\n".repeat(100) }));
  await page.goto(`${origin}/compound-gpid/dev/#page=modular-guide`);
  const toc = page.getByRole("navigation", { name: "On this page", exact: true });
  await expect(toc.getByRole("link")).toHaveCount(4);
  await expect(page.locator("[data-document] #repeat-1")).toBeVisible();
  await expect(page.locator(".callout-warning")).toContainText("<script>");
  expect(await page.evaluate(() => window.injected)).toBeUndefined();
  const link = toc.locator('a[data-section="repeat-1"]'); await link.focus(); await page.keyboard.press("Enter");
  await expect(page.locator("[data-document] #repeat-1")).toBeFocused();
  const top = await page.locator("[data-document] #repeat-1").evaluate(node => node.getBoundingClientRect().top);
  const header = await page.locator(".topbar").boundingBox(); expect(top).toBeGreaterThanOrEqual(header.y + header.height);
  const url = page.url(); await page.mouse.wheel(0, 500);
  expect(page.url()).toBe(url);
  await page.goto(`${origin}/compound-gpid/#home`);
  await expect(page.locator("[data-toc]")).toBeHidden();
});

test("short articles and loading states have no stale TOC; hidden references remain searchable", async ({ page }) => {
  await page.goto(`${origin}/compound-gpid/#page=modular-guide`);
  await expect(page.locator("[data-toc]")).toBeVisible();
  let release;
  const hold = new Promise(resolve => { release = resolve; });
  await page.route("**/research/index.md", async route => { await hold; await route.fulfill({ body: "# Short article\n## Only section\nRead this." }); });
  await page.evaluate(() => { location.hash = "page=research"; });
  await expect(page.locator("[data-document] [role=status]")).toHaveText("Loading documentation...");
  await expect(page.locator("[data-toc]")).toBeHidden(); release();
  await expect(page.locator("[data-document] h1")).toContainText("Short article");
  await expect(page.locator("[data-toc]")).toBeHidden();
  await page.getByRole("button", { name: "Search documentation", exact: true }).click();
  await page.locator("[data-search-input]").fill("cg-skill activate");
  await expect(page.locator(".search-result strong", { hasText: /^cg-skill activate$/ })).toBeVisible();
  await expect(page.locator('.search-result[href="#page=skill-management-activation"]')).toHaveCount(0);
});
