"use strict";
const { test, expect } = require("@playwright/test");
const fs = require("node:fs"), path = require("node:path"), os = require("node:os"), http = require("node:http");
const { modernSource } = require("./docs-publishing-fixture.js");
const { writeCombinedSite } = require("../assemble-docs-site.js");

module.exports = function identityCases() {
  test.describe("assembled channel identity", () => {
    let root, dev, legacy, paired, mixed, server, origin;
    test.beforeAll(async () => {
      root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "cg-browser-pair-"));
      dev = modernSource(); legacy = modernSource();
      const old = path.join(__dirname, "fixtures/docs-redesign/legacy/docs");
      fs.cpSync(old, path.join(legacy, "docs"), { recursive: true });
      const documents = require("./fixtures/docs-redesign/legacy-documents.json");
      for (const [file, text] of Object.entries(documents)) fs.writeFileSync(path.join(legacy, "docs", file), text);
      paired = path.join(root, "paired"); mixed = path.join(root, "mixed");
      const options = { mainRoot: dev, devRoot: dev, mainSha: "1".repeat(40), devSha: "2".repeat(40) };
      writeCombinedSite({ ...options, out: paired });
      writeCombinedSite({ ...options, mainRoot: legacy, out: mixed });
      server = http.createServer((request, response) => {
        const match = /^\/(paired|mixed)\/compound-gpid\/(.*)$/.exec(new URL(request.url, "http://localhost").pathname);
        if (!match || /%|\\|\.\./.test(match[2])) { response.writeHead(404).end(); return; }
        let file = match[2] || "index.html"; if (file.endsWith("/")) file += "index.html";
        try {
          const bytes = fs.readFileSync(path.join(root, match[1], "site", file));
          const type = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" };
          response.writeHead(200, { "Content-Type": type[path.extname(file)] || "text/plain", "Cache-Control": "no-store" }).end(bytes);
        } catch { response.writeHead(404).end(); }
      });
      await new Promise(resolve => server.listen(0, "127.0.0.1", resolve)); origin = `http://127.0.0.1:${server.address().port}`;
    });
    test.afterAll(async () => {
      if (server) await new Promise(resolve => server.close(resolve));
      for (const folder of [root, dev, legacy].filter(Boolean)) fs.rmSync(folder, { recursive: true, force: true });
    });

    for (const channel of ["", "dev/"]) test(`verified production identity and channel-local search ${channel || "root"}`, async ({ page }) => {
      const requested = []; page.on("request", r => requested.push(new URL(r.url()).pathname));
      await page.goto(`${origin}/paired/compound-gpid/${channel}#page=modular-guide&section=module-preferences`);
      await expect(page.locator("[data-build-identity]")).toHaveText(channel ? "Development: dev@22222222" : "Published: main@11111111");
      await expect(page.locator("[data-document] h1")).toBeVisible();
      await expect(page.locator("[data-document-source]")).toHaveAttribute("href", new RegExp(`/blob/${channel ? "2" : "1"}{40}/docs/modular-guide.md$`));
      await page.getByRole("button", { name: "Search documentation", exact: true }).click();
      await page.locator("[data-search-input]").fill("Module preferences");
      await expect(page.locator(".search-result").first()).toHaveAttribute("href", "#page=modular-guide&section=module-preferences");
      expect(requested.filter(p => p.endsWith("search-index.json"))).toEqual([`/paired/compound-gpid/${channel}assets/search-index.json`]);
      await page.keyboard.press("Escape");
      await page.locator("[data-channel-switch]").selectOption(channel ? "published" : "development");
      await expect(page).toHaveURL(new RegExp(`/compound-gpid/${channel ? "" : "dev/"}#page=modular-guide&section=module-preferences$`));
      await expect(page.locator("[data-build-identity]")).toHaveText(channel ? "Published: main@11111111" : "Development: dev@22222222");
    });

    for (const failure of ["metadata", "identity", "html", "script", "css", "helper"]) test(`rejects ${failure} integrity failure without a verified label`, async ({ page }) => {
      if (failure === "metadata") await page.route("**/channels.json", route => route.fulfill({ status: 503, body: "unavailable" }));
      if (failure === "identity") await page.route("**/channels.json", async route => {
        const response = await route.fetch(), data = await response.json(); data.channels.published.source.sha = "3".repeat(40);
        await route.fulfill({ json: data });
      });
      if (failure === "html") await page.route("**/paired/compound-gpid/", async route => {
        const response = await route.fetch(); const html = await response.text();
        await route.fulfill({ response, body: html.replace(/(name="cg-docs-shell" content=")[a-f0-9]{64}/, "$1" + "0".repeat(64)) });
      });
      const pattern = { script: /\/site\.[a-f0-9]{64}\.js$/, css: /\/site\.[a-f0-9]{64}\.css$/, helper: /\/docs-identity\.[a-f0-9]{64}\.js$/ }[failure];
      if (pattern) await page.route(pattern, route => route.fulfill({ contentType: failure === "css" ? "text/css" : "text/javascript", body: "/* stale response */" }));
      await page.goto(`${origin}/paired/compound-gpid/`);
      await expect(page.locator("[data-build-identity]")).toContainText("unverified");
      await expect(page.locator("[data-channel-switch]")).toBeDisabled();
      await expect(page.locator("[data-build-identity]")).not.toContainText("Published:");
    });

    for (const channel of ["", "dev/"]) test(`complete command browser uses verified channel-local facts ${channel || "root"}`, async ({ page }) => {
      const requests = []; page.on("request", request => { if (request.url().endsWith("command-index.json")) requests.push(new URL(request.url()).pathname); });
      await page.goto(`${origin}/paired/compound-gpid/${channel}#page=modular-guide`);
      await expect(page.locator("[data-build-identity]")).toContainText(channel ? "Development:" : "Published:");
      expect(requests).toHaveLength(0);
      await page.evaluate(() => { location.hash = "page=commands"; });
      await expect(page.locator(".command-card")).toHaveCount(57);
      expect(requests).toEqual([`/paired/compound-gpid/${channel}assets/command-index.json`]);
      await page.locator('[data-command-filter="query"]').fill("cg-help");
      await expect(page.locator(".command-card")).toHaveCount(2);
      await page.locator('[data-command-filter="suite"]').selectOption("cr");
      await page.locator('[data-command-filter="kind"]').selectOption("slash");
      await expect(page.locator(".command-card")).toHaveCount(1);
      await expect(page.locator(".command-card")).toHaveAttribute("data-command-id", "slash:cg-help");
      await page.locator(".command-card summary").click();
      await expect(page.locator(".command-card")).toContainText("Prerequisites");
      await expect(page.locator(".command-card")).toContainText("Constraints");
      await expect(page.locator(".command-card")).toContainText("Host certification is recorded separately");
      await page.locator('[data-command-filter="suite"]').selectOption("");
      await page.locator('[data-command-filter="kind"]').selectOption("workflow");
      await page.locator('[data-command-filter="query"]').fill("");
      await expect(page.locator(".command-card")).toHaveCount(4);
      const workflows = require("../../.github/shared/help-catalog.json").workflows;
      const commands = require("../../.github/shared/help-catalog.json").commands;
      for (const workflow of workflows) {
        const card = page.locator(`[data-command-id="workflow:${workflow.id}"]`); await card.locator("summary").click();
        await expect(card.locator("ol > li > code")).toHaveText(workflow.steps.map(step => commands.find(command => command.id === step.commandId).usage));
      }
    });

    test("cached command filters reject a changed deployment and cannot display mixed facts", async ({ page }) => {
      await page.goto(`${origin}/paired/compound-gpid/#page=commands`);
      await expect(page.locator(".command-card")).toHaveCount(57);
      await page.route("**/channels.json", async route => {
        const response = await route.fetch(), data = await response.json(); data.channels.published.source.sha = "3".repeat(40);
        await route.fulfill({ json: data });
      });
      await page.locator('[data-command-filter="query"]').fill("cg-help");
      await expect(page.locator(".command-browser [role=status]")).toContainText("Reload the full page");
      await expect(page.locator(".command-card")).toHaveCount(0);
      await expect(page.locator("[data-build-identity]")).toHaveText("Published: main@11111111");
    });

    test("forged command index fails channel digest verification", async ({ page }) => {
      await page.route("**/command-index.json", route => route.fulfill({ body: '{"commands":[]}' }));
      await page.goto(`${origin}/paired/compound-gpid/#page=commands`);
      await expect(page.locator("[data-build-notice]")).toContainText("digest mismatch");
      await expect(page.locator(".command-card")).toHaveCount(0);
    });

    test("an open tab retains its verified article when deployment metadata changes", async ({ page }) => {
      await page.goto(`${origin}/paired/compound-gpid/#page=modular-guide`);
      await expect(page.locator("[data-document] h1")).toBeVisible();
      const article = await page.locator("[data-document]").textContent();
      await page.route("**/channels.json", async route => {
        const response = await route.fetch(), data = await response.json(); data.channels.published.source.sha = "3".repeat(40);
        await route.fulfill({ json: data });
      });
      await page.evaluate(() => { location.hash = "page=research"; });
      await expect(page.locator("[data-build-notice]")).toContainText("build changed");
      await expect(page.locator("[data-document]")).toHaveText(article);
      await expect(page.locator("[data-build-identity]")).toHaveText("Published: main@11111111");
      await expect(page.locator("[data-build-reload]")).toBeVisible();
      await page.unroute("**/channels.json"); await page.locator("[data-build-reload]").click();
      await expect(page.locator("[data-document] h1")).toContainText("Research");
      await expect(page.locator("[data-build-notice]")).toBeHidden();
    });

    test("tampered fetched Markdown is rejected without replacing the verified article", async ({ page }) => {
      await page.goto(`${origin}/paired/compound-gpid/#page=modular-guide`);
      await expect(page.locator("[data-document] h1")).toBeVisible();
      await page.route("**/research/index.md", route => route.fulfill({ body: "# forged document" }));
      await page.evaluate(() => { location.hash = "page=research"; });
      await expect(page.locator("[data-build-notice]")).toContainText("digest mismatch");
      await expect(page.locator("[data-document] h1")).not.toContainText("forged");
    });

    test("legacy switching discloses limitations and keeps an exact return URL", async ({ page }) => {
      const returnUrl = `${origin}/mixed/compound-gpid/dev/#page=modular-guide&section=module-preferences`;
      await page.goto(returnUrl); await expect(page.locator("[data-document] h1")).toBeVisible();
      await page.locator("[data-channel-switch]").selectOption("published");
      const dialog = page.locator("[data-channel-dialog]"); await expect(dialog).toBeVisible();
      await expect(dialog).toContainText("no verified in-page identity");
      await expect(dialog.locator("[data-channel-return]")).toHaveValue(returnUrl);
      await dialog.locator("[data-channel-confirm]").click();
      await expect(page).toHaveURL(/\/mixed\/compound-gpid\/#page=modular-guide&section=module-preferences$/);
      await expect(page.locator("[data-channel-switch]")).toHaveCount(0);
      await page.goBack(); await expect(page).toHaveURL(returnUrl);
      await expect(page.locator("[data-build-identity]")).toHaveText("Development: dev@22222222");
    });

    test("missing upgraded sections disclose the fallback at departure and destination", async ({ page }) => {
      await page.goto(`${origin}/paired/compound-gpid/#page=modular-guide&section=missing-section`);
      await expect(page.locator("[data-document] h1")).toBeVisible();
      await page.locator("[data-channel-switch]").selectOption("development");
      await expect(page.locator("[data-channel-dialog]")).toContainText("page will open at the top");
      await page.locator("[data-channel-confirm]").click();
      await expect(page.locator("[data-channel-notice]")).toContainText("requested section is unavailable");
      await expect(page.locator("[data-channel-notice] a")).toHaveAttribute("href", /#page=modular-guide&section=missing-section$/);
    });

    test("missing legacy pages fall back to the old homepage without inventing new fragments", async ({ page }) => {
      await page.goto(`${origin}/mixed/compound-gpid/dev/#page=not-a-registered-page`);
      await expect(page.locator("[data-build-identity]")).toHaveText("Development: dev@22222222");
      await page.locator("[data-channel-switch]").selectOption("published");
      await expect(page.locator("[data-channel-dialog]")).toContainText("homepage will open");
      await page.locator("[data-channel-confirm]").click();
      await expect(page).toHaveURL(/\/mixed\/compound-gpid\/#home$/);
      await expect(page.locator("[data-home]")).toBeVisible();
      await expect(page.locator("[data-channel-notice]")).toHaveCount(0);
    });
  });
};
