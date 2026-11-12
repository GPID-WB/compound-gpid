"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { renderSite } = require("../render-docs-site.js");
const { checkRendered } = require("../check-rendered-docs.js");
const search = require("../../docs/assets/search-model.js");
const root = path.resolve(__dirname, "../..");

test("every guide is readable HTML with real links and search at both URL depths", () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "gpid-render-"));
  try {
    for (const channel of ["main", "dev"]) {
      const out = path.join(temp, channel === "main" ? "site" : "site/dev");
      const result = renderSite({ docsRoot: path.join(root, "docs"), out, channel, sha: "1".repeat(40) });
      assert.equal(checkRendered(out).pages, result.pages);
      const html = fs.readFileSync(path.join(out, "p-standard-first-workflow.html"), "utf8");
      assert.match(html, /<article[^>]*>\s*<h1[^>]*>Your First Standard Workflow<\/h1>/);
      assert.match(html, /<td>Two valid records<\/td>/);
      assert.match(html, /href="p-getting-started.html"/);
      assert.match(html, /href="#1-give-the-task-a-concrete-shape"/);
      assert.match(html, new RegExp(`blob/${channel}/docs/workflows/first-workflow.md`));
      assert.doesNotMatch(html, /href="#page=/);
      const index = JSON.parse(fs.readFileSync(path.join(out, "search-index.json"), "utf8"));
      const found = search.rank(index, "published poverty estimate")[0];
      assert.equal(found.id, "research-examples");
      assert.equal(found.section, "reproduce-a-published-poverty-estimate");
    }
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});

test("publication checks reject a broken section even when the page exists", () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "gpid-broken-"));
  try {
    renderSite({ docsRoot: path.join(root, "docs"), out: temp });
    const file = path.join(temp, "index.html");
    fs.appendFileSync(file, '<a href="p-research.html#nonexistent-section">Bad link</a>');
    assert.throws(() => checkRendered(temp), /missing anchor/);
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});

test("a Markdown edit updates both HTML and search without an editable second copy", () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "gpid-refresh-"));
  try {
    const docsRoot = path.join(temp, "docs");
    fs.cpSync(path.join(root, "docs"), docsRoot, { recursive: true });
    fs.appendFileSync(path.join(docsRoot, "workflows/standard.md"), "\n## Fresh example\n\nA new deterministic freshness probe.\n");
    const out = path.join(temp, "out");
    renderSite({ docsRoot, out });
    assert.match(fs.readFileSync(path.join(out, "p-standard-module.html"), "utf8"), /id="fresh-example"/);
    const index = JSON.parse(fs.readFileSync(path.join(out, "search-index.json"), "utf8"));
    assert.equal(search.rank(index, "deterministic freshness probe")[0].section, "fresh-example");
    assert.doesNotThrow(() => checkRendered(out));
    fs.writeFileSync(path.join(out, "p-retired-page.html"), "Obsolete output");
    renderSite({ docsRoot, out });
    assert.equal(fs.existsSync(path.join(out, "p-retired-page.html")), false);
    assert.throws(() => renderSite({ docsRoot, out: docsRoot }), /separate/);
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});

test("the new walkthroughs refer only to commands present in the plugin", () => {
  for (const file of ["workflows/standard.md", "workflows/first-workflow.md", "workflows/examples.md", "research/examples.md"]) {
    const markdown = fs.readFileSync(path.join(root, "docs", file), "utf8");
    for (const [, command] of markdown.matchAll(/\/((?:cg|cr)-[a-z]+(?:-[a-z]+)*)/g)) {
      assert.ok(fs.existsSync(path.join(root, ".github/prompts", `${command}.prompt.md`)), `${file}: ${command}`);
    }
  }
});
