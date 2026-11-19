"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const search = require("../../docs/assets/search-model.js");
const root = path.resolve(__dirname, "../..");
const page = (id, title, description = "") => ({ id, title, description, group: "Guide", file: `${id}.md` });

test("multi-word queries find the correct procedure and section irrespective of word order", () => {
  const index = search.records(page("install", "Installation"), "# Installation\n\n## Windows\nInstall using PowerShell.\n\n## macOS\nInstall using Bash.");
  const results = search.rank(index, "windows install");
  assert.equal(results.length, 1);
  assert.equal(results[0].section, "windows");
  assert.equal(search.rank(index, "windows postgres").length, 0);
});

test("exact command titles outrank incidental references and deduplicate pages", () => {
  const index = [
    ...search.records(page("overview", "Overview"), "# Overview\n\n## Tips\nTry cg-skill activate.\n\n## More\nAnother cg-skill activate mention."),
    ...search.records(page("activate", "`cg-skill activate`"), "# cg-skill activate\n\n## Usage\nActivate a skill."),
  ];
  const results = search.rank(index, "cg-skill activate");
  assert.equal(results[0].id, "activate");
  assert.equal(results.filter(entry => entry.id === "overview").length, 1);
  assert.equal(search.rank(index, "").length, 0);
});

test("rendered and searchable anchors agree, including punctuation, repeated headings, and code fences", () => {
  const context = vm.createContext({ DocsSearch: search, pageMap: new Map(), fileMap: new Map(), activePage: "" });
  vm.runInContext(fs.readFileSync(path.join(root, "docs/assets/markdown.js"), "utf8"), context);
  const markdown = '# A guide\n\n## Why Compound GPID?\nFirst.\n\n```text\n## Not a heading\n```\n\n## Why Compound GPID?\nSecond.';
  const html = context.markdownToHtml(markdown);
  const anchors = [...html.matchAll(/<h[2-6] id="([^"]+)"/g)].map(match => match[1]);
  const sections = search.records(page("guide", "A guide"), markdown).map(entry => entry.section).filter(Boolean);
  assert.deepEqual(anchors, ["why-compound-gpid", "why-compound-gpid-1"]);
  assert.deepEqual(sections, anchors);
});

test("all old documentation routes remain available exactly once", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/navigation.json"), "utf8"));
  const pages = manifest.groups.flatMap(group => group.pages);
  assert.equal(new Set(pages.map(page => page.id)).size, pages.length);
  assert.equal(new Set(pages.map(page => page.file)).size, pages.length);
  // Public entry points are compatibility contracts independent of visual group names.
  for (const id of ["getting-started", "installation", "research", "workflows", "reference", "manual", "skill-management", "skill-management-activate", "documentation-publishing"]) {
    assert.ok(pages.some(page => page.id === id), id);
  }
  for (const page of pages) assert.ok(fs.existsSync(path.join(root, "docs", page.file)), page.file);
});

test("real installation query opens the Windows section rather than a general mention", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/navigation.json"), "utf8"));
  const index = manifest.groups.flatMap(group => group.pages.flatMap(page => search.records({ ...page, group: group.title }, fs.readFileSync(path.join(root, "docs", page.file), "utf8"))));
  const first = search.rank(index, "install windows")[0];
  assert.equal(first.id, "installation");
  assert.match(first.section, /windows/);
});
