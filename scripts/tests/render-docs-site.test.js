"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
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
      assert.ok(html.includes(`blob/${"1".repeat(40)}/docs/workflows/first-workflow.md`));
      assert.ok(html.includes(`data-source-sha="${"1".repeat(40)}"`));
      assert.doesNotMatch(html, /href="#page=/);
      const index = JSON.parse(fs.readFileSync(path.join(out, "search-index.json"), "utf8"));
      const found = search.rank(index, "published poverty estimate")[0];
      assert.equal(found.id, "research-examples");
      assert.equal(found.section, "reproduce-a-published-poverty-estimate");
    }
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});

function renderMarkdown(markdown) {
  const context = vm.createContext({ DocsSearch: search });
  vm.runInContext(fs.readFileSync(path.join(root, "docs/assets/markdown.js"), "utf8"), context);
  return context.markdownToHtml(markdown);
}

test("inline code keeps literal operators, wildcards, and link syntax", () => {
  const markdown = "`2 * 3 * 4` and `/cg-*` and `/cr-*` and `[example](https://example.com)`; *try `x*y`*; [`name`](https://example.com)";
  const html = renderMarkdown(markdown);
  assert.match(html, /<code>2 \* 3 \* 4<\/code> and <code>\/cg-\*<\/code> and <code>\/cr-\*<\/code>/);
  assert.match(html, /<code>\[example\]\(https:\/\/example.com\)<\/code>/);
  assert.match(html, /<em>try <code>x\*y<\/code><\/em>/);
  assert.match(html, /<a [^>]*><code>name<\/code><\/a>/);
});

test("nested example fences stay literal in HTML and never become search sections", () => {
  const markdown = ["Intro", "  ````md", "```", "## Inside short fence", "~~~~", "## Inside mixed fence",
    "````not-a-close", "## Inside suffixed fence", "  ````` \t", "~~", "  ~~~md", "## Inside tilde fence",
    "~~~", "## Real heading"].join("\r\n");
  const html = renderMarkdown(markdown);
  assert.match(html, /class="language-md">```\n## Inside short fence/);
  assert.match(html, /````not-a-close\n## Inside suffixed fence<\/code>/);
  assert.match(html, /class="language-md">## Inside tilde fence<\/code>/);
  assert.deepEqual([...html.matchAll(/<h2 id="([^"]+)"/g)].map(match => match[1]), ["real-heading"]);
  assert.deepEqual(search.records({}, markdown).map(record => record.section), ["", "real-heading"]);
});

test("front matter needs exact three-hyphen delimiter lines in HTML and search", () => {
  const rules = ["----", "## Important", "Body", "----", "## Next"].join("\n");
  assert.equal((renderMarkdown(rules).match(/<hr>/g) || []).length, 2);
  assert.match(renderMarkdown(rules), /<h2 id="important">Important<\/h2>/);
  assert.deepEqual(search.records({}, rules).slice(1).map(record => record.section), ["important", "next"]);

  const metadata = ["\uFEFF---", "note: |", "  ----", "  ## Private metadata", "---", "## Next"].join("\r\n");
  assert.equal(renderMarkdown(metadata), '<h2 id="next">Next</h2>');
  const records = search.records({}, metadata);
  assert.deepEqual(records.map(record => record.section), ["", "next"]);
  assert.equal(records[0].text, "");
});

test("search skips real comments without swallowing fences or later sections", () => {
  const markdown = ["<!--", "## Hidden", "```", "-->", "```html", "<!--", "```",
    "## Visible", "-->", "## Later", "Text <!-- Hidden phrase --> after the comment."].join("\n");
  const html = renderMarkdown(markdown);
  assert.match(html, /<code class="language-html">&lt;!--<\/code>/);
  assert.deepEqual([...html.matchAll(/<h2 id="([^"]+)"/g)].map(match => match[1]), ["visible", "later"]);
  const records = search.records({}, markdown);
  assert.deepEqual(records.map(record => record.section), ["", "visible", "later"]);
  assert.doesNotMatch(records[2].text, /Hidden phrase/);
});

test("heading IDs are unique and match search anchors when suffixes collide", () => {
  for (const [headings, expected] of [
    [["Setup", "Setup", "Setup-1"], ["setup", "setup-1", "setup-1-1"]],
    [["Setup", "Setup-1", "Setup"], ["setup", "setup-1", "setup-2"]],
  ]) {
    const markdown = headings.map(heading => `## ${heading}`).join("\n");
    const html = renderMarkdown(markdown);
    assert.deepEqual([...html.matchAll(/<h2 id="([^"]+)"/g)].map(match => match[1]), expected);
    assert.deepEqual(search.records({}, markdown).slice(1).map(record => record.section), expected);
  }
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
    const html = fs.readFileSync(path.join(out, "p-standard-module.html"), "utf8");
    assert.match(html, /id="fresh-example"/);
    assert.match(html, /blob\/dev\/docs\/workflows\/standard.md/);
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
