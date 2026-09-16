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
const contentEdits = require("./fixtures/docs-redesign/phase2-content-edits.json");
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

const normalizeProse = text => text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/^#{1,6}\s+/gm, "").replace(/\s+/g, " ").trim();

test("all 29 management entries and importing content retain every safety/example/context block", () => {
  assert.equal(inventory.preservation.length, 30);
  assert.equal(inventory.preservation.filter(page => page.file.startsWith("skills/management/")).length, 29);
  assert.equal(inventory.preservation.filter(page => page.file.includes("/commands/")).length, 12);
  const lost = [];
  for (const page of inventory.preservation) {
    const actual = read(page.file).replace(/\r\n/g, "\n");
    assert.ok(page.plannedDestination.page);
    assert.ok(page.blocks.length);
    const migrated = pages.find(p => p.id === page.id).redirect || page.id === "skill-management";
    const destination = migrated ? `${actual}\n${read("skills/management/index.md")}` : actual;
    for (const block of page.blocks) {
      const edit = page.file === contentEdits.source && contentEdits.edits.find(edit => block.text.startsWith(edit.oldPrefix));
      const required = edit ? edit.required : [block.text];
      for (const text of required) if (!normalizeProse(destination).includes(normalizeProse(text))) lost.push(`${page.file}: ${text}`);
    }
    if (!migrated) assert.equal(hash(actual), page.sourceSha256, `Operation contract changed: ${page.file}`);
  }
  assert.deepEqual(lost, []);
  for (const edit of contentEdits.edits) {
    assert.equal(inventory.preservation.find(p => p.file === contentEdits.source).blocks.filter(b => b.text.startsWith(edit.oldPrefix)).length, 1);
    assert.ok(edit.reason); assert.ok(fs.existsSync(path.join(root, edit.authority)));
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
    // Editorial links can move during consolidation; every frozen public destination still resolves.
    if (!link.source.startsWith("docs/")) assert.ok(source.includes(link.href), `Lost canonical consumer link from ${link.source}: ${link.href}`);
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
  const guide = read("skills/management/index.md");
  assert.ok(normalizeProse(guide).includes(normalizeProse(safety.text)));
  const changed = guide.replace(safety.text, "Omitted safety condition.");
  assert.equal(normalizeProse(changed).includes(normalizeProse(safety.text)), false);
});

test("release-note refresh preserves all manual prose outside the owned marker pair", () => {
  const { normalizeManagedInteriors, findManagedMarkers } = require("../docs-markers.js");
  const before = legacyDocuments["whats-new.md"], after = read("whats-new.md");
  assert.deepEqual(findManagedMarkers(after).map(marker => marker.section), ["release-notes"]);
  assert.equal(normalizeManagedInteriors(after), normalizeManagedInteriors(before));
  assert.notEqual(normalizeManagedInteriors(`Changed prose\n${after}`), normalizeManagedInteriors(before));
});

test("phase 2 has one complete skill guide and useful redirected raw narratives", () => {
  const guide = read("skills/management/index.md");
  const required = ["Start Here", "Lifecycle and Safety", "Use Skills in a Project", "Maintain Plugin Skills",
    "Security and Provenance", "Diagnose and Recover", "Migrate Existing Workflows", "Operation Reference"];
  assert.deepEqual(contract.extractHeadings(guide).filter(h => h.level === 2).map(h => h.text), required);
  for (const old of inventory.preservation.filter(p => !p.file.includes("/commands/") && p.id !== "skill-management")) {
    const page = pages.find(p => p.id === old.id);
    assert.equal(page.sidebar, false, old.id);
    assert.equal(page.redirect?.page, "skill-management", old.id);
    assert.match(read(old.file), /\[.*\]\([^)]*index\.md#/, old.file);
  }
});

test("phase 2 primary navigation is task based and references remain registered", () => {
  assert.deepEqual(manifest.groups.map(g => g.title), ["Start Here", "Technical Workflows", "Research Workflows", "Skills", "Operate", "Reference", "Contribute"]);
  const skills = manifest.groups.find(g => g.title === "Skills");
  assert.deepEqual(skills.pages.filter(contract.sidebarVisible).map(p => p.id), ["skills", "skill-management"]);
  for (const page of pages.filter(p => p.file.includes("/commands/"))) {
    assert.equal(page.sidebar, false); assert.equal(contract.searchable(page), true);
  }
});

test("all frozen redirected headings reach valid unified sections and contracts keep their paths", () => {
  const byId = new Map(pages.map(p => [p.id, p]));
  for (const baseline of inventory.routes) {
    const page = byId.get(baseline.id);
    if (!page.redirect) continue;
    for (const heading of baseline.headings) {
      for (const section of new Set([heading.destination.section, heading.legacyRuntime, heading.legacyValidator].filter(Boolean))) {
        const destination = contract.resolveRoute(pages, page.id, section);
        const target = byId.get(destination.page);
        assert.equal(contract.resolveSection(contract.extractHeadings(read(target.file)), destination.section, target.sectionAliases).status, "resolved", `${page.id}#${section}`);
      }
    }
  }
  const operations = path.join(root, ".github/shared/skill-management/operations");
  const descriptors = fs.readdirSync(operations).filter(name => name.endsWith(".json"));
  assert.equal(descriptors.length, 12);
  for (const name of descriptors) {
    const descriptor = JSON.parse(fs.readFileSync(path.join(operations, name)));
    const page = pages.find(p => `docs/${p.file}` === descriptor.documentation);
    assert.ok(page); assert.equal(page.redirect, undefined);
    assert.match(read(page.file), /\.\.\/index\.md#result-contract/);
  }
});

test("every shipped slash prompt and shell wrapper has a complete editorial checklist row", () => {
  const hub = read("reference/commands.md");
  const prompts = fs.readdirSync(path.join(root, ".github/prompts")).filter(name => name.endsWith(".prompt.md")).map(name => name.replace(".prompt.md", ""));
  const wrappers = [...new Set(fs.readdirSync(path.join(root, "bin")).filter(name => name.startsWith("cg-")).map(name => name.replace(/\.cmd$/, "")))];
  for (const command of [...prompts.map(name => `/${name}`), ...wrappers]) {
    const row = hub.split("\n").find(line => line.startsWith(`| \`${command} `) || line.startsWith(`| \`${command}\``));
    // The discovery table is not the entry checklist: require the five substantive cells.
    const rows = hub.split("\n").filter(line => line.startsWith(`| \`${command} `) || line.startsWith(`| \`${command}\``));
    assert.ok(row && rows.some(line => line.split(" | ").length >= 5), command);
  }
  const recipes = contract.extractHeadings(read("workflows/index.md")).filter(h => h.level === 3).map(h => h.text);
  for (const title of ["Start a Project", "Fix a Software Error", "Complete a Small Technical Task", "Deliver a Larger Change", "Resolve Review Findings", "Run Research", "Resume or Recover", "Manage Skills"]) assert.ok(recipes.includes(title), title);
});
