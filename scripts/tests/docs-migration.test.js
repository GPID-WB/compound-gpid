"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "../..");
const fixture = path.join(__dirname, "fixtures/docs-redesign");
const inventory = require("./fixtures/docs-redesign/migration-inventory.json");
const legacyDocuments = require("./fixtures/docs-redesign/legacy-documents.json");
const contract = require("../../docs/assets/docs-contract.js");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/navigation.json")));
const pages = contract.validateManifest(manifest);
const hash = value => crypto.createHash("sha256").update(value).digest("hex");
const read = file => fs.readFileSync(path.join(root, "docs", file), "utf8");

function renderer(file, shared = false) {
  const context = vm.createContext({ document: { querySelector: () => ({}) }, URLSearchParams,
    location: { hash: "" }, ...(shared ? { DocsContract: contract } : {}) });
  const source = fs.readFileSync(file, "utf8");
  vm.runInContext(source.slice(0, source.indexOf('document.querySelectorAll("[data-open-search]")')), context);
  return markdown => vm.runInContext(`markdownToHtml(${JSON.stringify(markdown)})`, context);
}

test("all 76 baseline routes and every heading have explicit retained destinations", () => {
  assert.equal(inventory.routes.length, 76);
  const render = renderer(path.join(root, "docs/assets/site.js"), true);
  for (const baseline of inventory.routes) {
    const page = pages.find(page => page.id === baseline.destination.page);
    assert.ok(page, baseline.id); assert.equal(page.file, baseline.destination.file);
    const text = read(page.file), headings = contract.extractHeadings(text);
    const htmlIds = [...render(text).matchAll(/<h\d id="([^"]+)"/g)].map(m => m[1]);
    assert.deepEqual(htmlIds, headings.map(h => h.id), page.id);
    assert.equal(new Set(htmlIds).size, htmlIds.length, page.id);
    for (const heading of baseline.headings) {
      assert.ok(headings.some(h => h.id === heading.destination.section), `${page.id}#${heading.destination.section}`);
      for (const alias of [heading.legacyRuntime, heading.legacyValidator].filter(Boolean)) {
        assert.equal(contract.resolveSection(headings, alias, page.sectionAliases).status, "resolved", `${page.id}#${alias}`);
      }
    }
    assert.deepEqual(page.sectionAliases || {}, Object.fromEntries(Object.entries(baseline.aliasDecisions).map(([alias, decision]) => [alias, decision.target])), page.id);
    for (const alias of baseline.legacyRenderedIds.filter(Boolean)) {
      assert.equal(contract.resolveSection(headings, alias, page.sectionAliases).status, "resolved", `${page.id}#${alias}`);
    }
  }
});

test("all 29 management entries and importing content retain every safety/example/context block", () => {
  assert.equal(inventory.preservation.length, 30);
  assert.equal(inventory.preservation.filter(page => page.file.startsWith("skills/management/")).length, 29);
  assert.equal(inventory.preservation.filter(page => page.file.includes("/commands/")).length, 12);
  for (const page of inventory.preservation) {
    const actual = read(page.file).replace(/\r\n/g, "\n");
    assert.ok(page.plannedDestination.page);
    assert.ok(page.blocks.length);
    for (const block of page.blocks) assert.ok(actual.includes(block.text), `Lost ${block.kind}: ${page.file}: ${block.text.slice(0, 80)}`);
    assert.equal(hash(actual), page.sourceSha256, `Unreviewed content change: ${page.file}`);
  }
});

test("captured legacy runtime executes with its real old slug and duplicate behavior", () => {
  const legacy = renderer(path.join(fixture, "legacy/docs/assets/site.js"));
  const example = "# A/B\n## A/B\n## Caf\u00e9";
  assert.deepEqual([...legacy(example).matchAll(/<h\d id="([^"]+)"/g)].map(m => m[1]), ["a-b", "a-b", "caf"]);
  for (const baseline of inventory.routes) {
    assert.equal(hash(legacyDocuments[baseline.file]), baseline.sourceSha256, baseline.file);
    assert.deepEqual([...legacy(legacyDocuments[baseline.file]).matchAll(/<h\d id="([^"]*)"/g)].map(m => m[1]), baseline.legacyRenderedIds, baseline.file);
  }
});

test("inventory covers current source inbound links and resolves registered page fragments", () => {
  assert.equal(inventory.inboundLinks.length, 347);
  const byFile = new Map(pages.map(page => [`docs/${page.file}`, page]));
  for (const link of inventory.inboundLinks) {
    const source = fs.readFileSync(path.join(root, link.source), "utf8");
    assert.ok(source.includes(link.href), `Lost inbound link from ${link.source}: ${link.href}`);
    if (link.href.startsWith("#page=")) {
      const route = new URLSearchParams(link.href.slice(1));
      assert.ok(pages.some(page => page.id === route.get("page")), link.href);
      continue;
    }
    const page = byFile.get(link.target);
    if (!page) continue; // Non-page assets and candidate-only paths have separate validator coverage.
    if (link.fragment) assert.equal(contract.resolveSection(contract.extractHeadings(read(page.file)), decodeURIComponent(link.fragment), page.sectionAliases).status, "resolved", link.href);
  }
});

test("preservation checks detect safety loss, not just a matching file inventory", () => {
  const security = inventory.preservation.find(page => page.id === "skill-management-security");
  const safety = security.blocks.find(block => block.kind === "safety");
  assert.ok(safety);
  const changed = read(security.file).replace(safety.text, "Omitted safety condition.");
  assert.equal(changed.includes(safety.text), false);
  assert.notEqual(hash(changed), security.sourceSha256);
});

test("release-note refresh preserves all manual prose outside the owned marker pair", () => {
  const { normalizeManagedInteriors, findManagedMarkers } = require("../docs-markers.js");
  const before = legacyDocuments["whats-new.md"], after = read("whats-new.md");
  assert.deepEqual(findManagedMarkers(after).map(marker => marker.section), ["release-notes"]);
  assert.equal(normalizeManagedInteriors(after), normalizeManagedInteriors(before));
  assert.notEqual(normalizeManagedInteriors(`Changed prose\n${after}`), normalizeManagedInteriors(before));
});
