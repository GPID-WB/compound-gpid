"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const generate = data => require("../docs-search-index.js").generateSearchIndex(data);
const search = () => require("../../docs/assets/docs-search.js");
const page = (id, extra = {}) => ({ id, file: `${id}.md`, title: id, description: `Read ${id}`, ...extra });
const registry = {
  modules: [{ id: "kernel", layer: "kernel" }, { id: "suite-cg", layer: "suite" },
    { id: "suite-cr", layer: "suite" }, { id: "cap-skills", layer: "capability" }],
  capabilities: [{ owningModule: "cap-skills", supportedSuites: ["cg", "cr"] }],
};
function fixture() {
  return { registry, manifest: { schemaVersion: "compound-gpid-docs-navigation-v1", groups: [
    { title: "Read", ownerModule: "kernel", pages: [page("guide", { title: "Find a command" }),
      page("shell", { title: "cg-skill", ownerModule: "cap-skills", sidebar: false }),
      page("technical", { title: "/cg-skill", ownerModule: "suite-cg" }),
      page("research", { ownerModule: "suite-cr" }),
      page("old", { redirect: { page: "guide", sections: {} } })] },
  ] }, documents: {
    "guide.md": "# Find a command\nIntro.\n## Choose\nRead /cg-skill and cg-skill.\n## Repeat\nFirst.\n## Repeat\nSecond.\n```md\n## Hidden\n```",
    "shell.md": "# cg-skill\nShell command.\n## Inspect\ncg-skill inspect example",
    "technical.md": "# /cg-skill\nSlash prompt.\n## Review\n/cg-skill inspect example",
    "research.md": "# Research\n## Evidence\nCompare surveys.",
    "old.md": "# Old\nOnly an obsolete narrative.",
  } };
}

test("section generation repeats byte-for-byte without modifying inputs or indexing derived data", () => {
  const input = fixture(), before = JSON.stringify(input);
  const first = generate(input);
  assert.equal(generate(input), first);
  assert.equal(JSON.stringify(input), before);
  input.documents["assets/search-index.json"] = "must-not-be-indexed";
  assert.equal(generate(input), first);
  assert.ok(first.endsWith("\n"));
  assert.equal(JSON.parse(first).headingContract, "compound-gpid-headings-v2");
});

test("hidden references are indexed, compatibility stubs are excluded, and headings use shared IDs", () => {
  const entries = JSON.parse(generate(fixture())).entries;
  assert.ok(entries.some(row => row.page === "shell"));
  assert.ok(!entries.some(row => row.page === "old"));
  assert.deepEqual(entries.filter(row => row.page === "guide").map(row => row.section), [null, "choose", "repeat", "repeat-1"]);
  assert.ok(!entries.some(row => row.section === "hidden"));
  assert.equal(entries.find(row => row.section === "repeat").text, "First.");
});

test("suite labels come from canonical ownership and support, never command spelling", () => {
  const entries = JSON.parse(generate(fixture())).entries;
  for (const [id, suite] of Object.entries({ guide: "shared", shell: "shared", technical: "cg", research: "cr" })) {
    assert.ok(entries.filter(row => row.page === id).every(row => row.suite === suite));
  }
});

test("generation rejects missing source, unknown ownership, and ambiguous capability support", () => {
  const missing = fixture(); delete missing.documents["shell.md"];
  assert.throws(() => generate(missing), /missing.*shell.md/i);
  const unknown = fixture(); unknown.manifest.groups[0].pages[0].ownerModule = "unknown";
  assert.throws(() => generate(unknown), /owner/i);
  const ambiguous = fixture();
  ambiguous.registry = structuredClone(registry);
  ambiguous.registry.capabilities.push({ owningModule: "cap-skills", supportedSuites: ["cg"] });
  assert.throws(() => generate(ambiguous), /support/i);
});

test("unsafe source paths are rejected before document lookup", () => {
  for (const file of ["../outside.md", "https://other.test/x.md", "%2e%2e/x.md", "a\\b.md"]) {
    const input = fixture(); input.manifest.groups[0].pages[0].file = file;
    assert.throws(() => generate(input), /unsafe/i);
  }
});

test("nested and Unicode headings keep the rendered section contract", () => {
  const input = fixture();
  input.documents["guide.md"] = "# Guide\n> ## Caf\u00e9 `API()`\n> Evidence.\n\n- Entry\n  ### Details\n  Nested body.\n\n## Details\nFinal.";
  const entries = JSON.parse(generate(input)).entries.filter(row => row.page === "guide");
  assert.deepEqual(entries.map(row => row.section), [null, "caf\u00e9-api", "details", "details-1"]);
  assert.match(entries.find(row => row.section === "details").text, /Nested body/);
});

test("index validation fails closed on schema, incomplete coverage, duplicate entries, or extra URL fields", () => {
  const input = fixture(), index = JSON.parse(generate(input));
  assert.equal(search().validateIndex(index, input.manifest), index);
  for (const change of [value => { value.schemaVersion = "unknown"; },
    value => { value.headingContract = "unknown"; }, value => { value.entries = []; },
    value => { value.entries.push(value.entries[0]); }, value => { value.entries[0].url = "javascript:alert(1)"; },
    value => { value.entries[0].page = "old"; }, value => { value.entries[0].section = "../outside"; },
    value => { value.entries[0].suite = "trusted"; }, value => { value.entries[0].title = "Forged title"; }]) {
    const changed = structuredClone(index); change(changed);
    assert.throws(() => search().validateIndex(changed, input.manifest), /search/i);
  }
});

test("exact titles rank above body mentions and slash and shell tokens remain distinct", () => {
  const index = JSON.parse(generate(fixture()));
  assert.equal(search().rank(index, "/cg-skill")[0].page, "technical");
  assert.equal(search().rank(index, "cg-skill")[0].page, "shell");
  assert.ok(!search().rank(index, "/cg-skill").some(row => row.page === "shell"));
  assert.ok(!search().rank(index, "cg-skill").some(row => row.page === "technical"));
  assert.equal(search().rank(index, "Find a command")[0].page, "guide");
});

test("exact headings outrank incidental text and results link to deterministic sections", () => {
  const input = fixture(); input.documents["shell.md"] += "\n\n## Other\nCompare surveys and evidence.";
  const index = JSON.parse(generate(input));
  assert.equal(search().rank(index, "evidence")[0].section, "evidence");
  assert.equal(search().rank(index, "Second")[0].section, "repeat-1");
  assert.deepEqual(search().rank(index, "not-present"), []);
  assert.deepEqual(search().rank(index, "  "), []);
});

test("ranking is deterministic, bounds each page, and avoids duplicate narrative hits", () => {
  const input = fixture();
  input.documents["guide.md"] += Array.from({ length: 20 }, (_, i) => `\n## Find ${i}\nCompare surveys ${i}.`).join("");
  input.documents["technical.md"] += "\n## Evidence\nCompare surveys.";
  const index = JSON.parse(generate(input)), results = search().rank(index, "surveys");
  assert.deepEqual(search().rank(index, "surveys"), results);
  assert.ok(results.length >= 2);
  assert.ok(results.filter(row => row.page === "guide").length <= 2);
  assert.equal(results.filter(row => row.heading === "Evidence" && row.text === "Compare surveys.").length, 1);
  assert.ok(results.length <= 12);
});

test("script-like Markdown remains inert data and snippets are bounded plain text", () => {
  const input = fixture(); input.documents["guide.md"] = '# Guide\n## Safety\n<script>global.injected=true</script> & "quoted" ' + "word ".repeat(100);
  const index = JSON.parse(generate(input)), result = search().rank(index, "injected")[0];
  assert.equal(global.injected, undefined);
  assert.match(result.snippet, /injected/);
  assert.ok(result.snippet.length <= 180);
  assert.equal(result.page, "guide");
  assert.equal(result.section, "safety");
});

for (const [kind, body] of [
  ["inline", "Set `KILO_DISABLE_EXTERNAL_SKILLS=1`."],
  ["fenced", "```sh\nKILO_DISABLE_EXTERNAL_SKILLS=1\n```"],
  ["plain", "Set KILO_DISABLE_EXTERNAL_SKILLS=1."],
]) test(`underscore identifiers survive ${kind} text and exact search queries`, () => {
  const input = fixture(); input.documents["guide.md"] = `# Guide\n## Environment\n${body}`;
  const index = JSON.parse(generate(input));
  const entry = index.entries.find(row => row.page === "guide" && row.section === "environment");
  assert.ok(entry.text.includes("KILO_DISABLE_EXTERNAL_SKILLS=1"));
  for (const query of ["KILO_DISABLE_EXTERNAL_SKILLS", "kilo_disable_external_skills"]) {
    const result = search().rank(index, query)[0];
    assert.equal(result?.page, "guide");
    assert.equal(result.section, "environment");
    assert.ok(result.snippet.includes("KILO_DISABLE_EXTERNAL_SKILLS=1"));
  }
});

test("search text removes supported formatting delimiters, not literal code characters", () => {
  const input = fixture();
  input.documents["guide.md"] = '# Guide\n## **Use `some_identifier`**\n'
    + '**bold_identifier** and *em_identifier* with [a_link](target.md). '
    + 'Keep `*literal_* [not_a_link](target.md)` and bare_identifier.\n\n'
    + '```text\n**literal_code** [a_link](target.md) `back_ticks`\n```';
  const entry = JSON.parse(generate(input)).entries.find(row => row.page === "guide" && row.section !== null);
  assert.equal(entry.heading, "Use some_identifier");
  assert.equal(entry.text, 'bold_identifier and em_identifier with a_link. '
    + 'Keep *literal_* [not_a_link](target.md) and bare_identifier. '
    + '**literal_code** [a_link](target.md) `back_ticks`');
});

test("current canonical pages produce a complete validated index with no source writes", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/navigation.json")));
  const documents = Object.fromEntries(manifest.groups.flatMap(group => group.pages).map(row =>
    [row.file, fs.readFileSync(path.join(root, "docs", row.file), "utf8")]));
  const input = { manifest, documents, registry: JSON.parse(fs.readFileSync(path.join(root, ".github/shared/module-registry.json"))) };
  const before = JSON.stringify(input), output = generate(input), index = JSON.parse(output);
  search().validateIndex(index, manifest);
  assert.equal(generate(input), output);
  assert.equal(JSON.stringify(input), before);
  assert.ok(index.entries.length > 100);
  assert.ok(search().rank(index, "cg-skill activate").some(row => row.page === "skill-management-activate"));
  assert.ok(search().rank(index, "KILO_DISABLE_EXTERNAL_SKILLS")
    .some(row => row.page === "installation" && row.snippet.includes("KILO_DISABLE_EXTERNAL_SKILLS")));
});
