"use strict";
const test = require("node:test"), assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const { prepareHelp } = require("../docs-help-build.js");
const { modernSource } = require("./docs-publishing-fixture.js");

test("documents and browser facts use the same validated catalog snapshot", t => {
  const root = modernSource(); t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const file = path.join(root, ".github/shared/help-catalog.json"), original = JSON.parse(fs.readFileSync(file));
  const cp = require("node:child_process"), execute = cp.execFileSync;
  cp.execFileSync = (...args) => {
    const result = execute(...args), changed = structuredClone(original);
    changed.commands[0].summary = "MUTATED AFTER VALIDATION"; fs.writeFileSync(file, JSON.stringify(changed));
    return result;
  };
  const modulePath = require.resolve("../docs-help-build.js"); delete require.cache[modulePath];
  try {
    const result = require(modulePath).prepareHelp(root);
    assert.equal(result.projection.commands[0].summary, original.commands[0].summary);
  } finally { cp.execFileSync = execute; delete require.cache[modulePath]; }
});

test("complete catalog projection preserves kind IDs, shared eligibility and repeated workflow steps", () => {
  const build = prepareHelp(path.resolve(__dirname, "../.."));
  const catalog = require("../../.github/shared/help-catalog.json");
  assert.equal(build.projection.commands.length, catalog.commands.length);
  assert.equal(build.projection.sourceDigest, catalog.sourceDigest);
  assert.ok(build.projection.commands.find(c => c.id === "slash:cg-help"));
  assert.ok(build.projection.commands.find(c => c.id === "shell:cg-help"));
  for (const w of catalog.workflows) assert.deepEqual(build.projection.workflows.find(x => x.id === w.id).steps, w.steps);
});

test("catalog projection rejects missing routes, renamed headings and stale canonical facts", t => {
  const root = modernSource(); t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const file = path.join(root, "docs/reference/command-routes.json"), original = fs.readFileSync(file);
  const routes = JSON.parse(original); delete routes.routes["slash:cg-help"]; fs.writeFileSync(file, JSON.stringify(routes));
  assert.throws(() => prepareHelp(root), /route inventory/); fs.writeFileSync(file, original);
  const page = path.join(root, "docs/reference/commands.md"), text = fs.readFileSync(page, "utf8");
  fs.writeFileSync(page, text.replace("## Technical Entry Checklist", "## Renamed"));
  assert.throws(() => prepareHelp(root), /route heading/); fs.writeFileSync(page, text);
  fs.appendFileSync(path.join(root, ".github/prompts/cg-help.prompt.md"), "\nchanged\n");
  assert.throws(() => prepareHelp(root), /stale|validation/);
});

test("browser projection validates all rows and preserves shared and kind-specific selection", () => {
  const browser = require("../../docs/assets/docs-commands.js"), value = prepareHelp(path.resolve(__dirname, "../..")).projection;
  browser.validate(value);
  for (const suite of ["cg", "cr"]) assert.ok(browser.select(value, suite, "slash", "cg-help").some(c => c.id === "slash:cg-help"));
  assert.deepEqual(browser.select(value, "", "shell", "cg-help").map(c => c.id), ["shell:cg-help"]);
  assert.ok(browser.select(value, "", "", "").length > 3);
  const repeated = structuredClone(value); const workflow = repeated.workflows[0];
  workflow.steps.push({ ...workflow.steps[0], order: workflow.steps.length + 1 });
  browser.validate(repeated);
  assert.equal(browser.select(repeated, "", "workflow", "")[0].steps.at(-1).commandId, workflow.steps[0].commandId);
  for (const mutate of [
    data => { data.commands.push(data.commands[0]); },
    data => { data.commands[0].route.page = "javascript:alert(1)"; },
    data => { data.commands[0].route.section = "../elsewhere"; },
    data => { data.commands[0].examples = [null]; },
    data => { data.commands[0].relatedCommands = [{ id: "slash:missing", relation: "next" }]; },
    data => { data.workflows[0].steps[0].order = 3; },
  ]) { const bad = structuredClone(value); mutate(bad); assert.throws(() => browser.validate(bad)); }
});

test("v3 fingerprint binds catalog inputs and raw wrapper bytes while excluding only derived indexes", t => {
  const root = modernSource(); t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const fingerprint = () => require("../docs-fingerprint.js").fingerprint(root, 3), original = fingerprint();
  for (const file of ["docs/assets/search-index.json", "docs/assets/command-index.json"]) fs.writeFileSync(path.join(root, file), "changed derived output");
  assert.equal(fingerprint(), original);
  for (const file of ["docs/reference/command-routes.json", ".github/shared/help-catalog.json", ".github/prompts/cg-help.help.json", "scripts/help/documentation.py", "scripts/schemas/help_catalog_schema.json", "bin/cg-help.cmd"]) {
    const target = path.join(root, file), bytes = fs.readFileSync(target);
    fs.appendFileSync(target, "\n"); assert.notEqual(fingerprint(), original, file); fs.writeFileSync(target, bytes);
  }
  const wrapper = path.join(root, "bin/cg-help.cmd"), bytes = fs.readFileSync(wrapper);
  fs.writeFileSync(wrapper, bytes.toString().replace(/\r\n/g, "\n")); assert.notEqual(fingerprint(), original);
});

test("captured v2 producer remains independently verifiable; mixed v2/v3 identity claims are rejected", t => {
  const root = modernSource(), current = modernSource();
  const work = fs.mkdtempSync(path.join(require("node:os").tmpdir(), "cg-v2-recovery-"));
  t.after(() => [root, current, work].forEach(dir => fs.rmSync(dir, { recursive: true, force: true })));
  fs.cpSync(path.resolve(__dirname, "../docs-legacy-v2"), root, { recursive: true });
  for (const name of ["reference.md", "reference/commands.md"]) fs.copyFileSync(path.join(__dirname, "fixtures/help-docs", name), path.join(root, "docs", name));
  const provenance = require("../docs-provenance.js"), controller = require("../assemble-docs-site.js");
  assert.equal(provenance.identifyProducer(root).fingerprintVersion, 2);
  assert.equal(require("../docs-fingerprint.js").fingerprint(root, 2), require("../docs-legacy-v2/scripts/docs-fingerprint.js").fingerprint(root, 2));
  const options = { mainRoot: root, devRoot: root, mainSha: "1".repeat(40), devSha: "2".repeat(40), out: path.join(work, "pair") };
  controller.writeCombinedSite(options); assert.equal(controller.verifyCombinedSite(options.out, root, root, options), 0);
  assert.throws(() => controller.writeCombinedSite({ ...options, devRoot: current }), /v2 recovery cannot be paired/);
});

test("native help guidance matches current source-bound support evidence", () => {
  const root = path.resolve(__dirname, "../.."), relative = ".cg-docs/work-reports/2026-09-23-docs-help-support.json";
  const proof = JSON.parse(fs.readFileSync(path.join(root, relative)));
  require("node:child_process").execFileSync(process.platform === "win32" ? "python" : "python3",
    [path.join(root, "scripts/cg_verify_help_support.py"), "--root", root, "--evidence", relative], { timeout: 30000 });
  const text = fs.readFileSync(path.join(root, "docs/help/index.md"), "utf8");
  const names = { "claude-code": "Claude Code", codex: "Codex", copilot: "GitHub Copilot", kilo: "Kilo", opencode: "OpenCode" };
  for (const row of proof.platforms) {
    const expected = row.runtimeStatus === "verified" ? "Verified" : "Unverified";
    assert.ok(text.includes(`| ${names[row.platform]} | ${expected} |`), row.platform);
  }
  assert.ok(text.includes(proof.subjectCommit));
  assert.ok(text.includes("only for the verified Kilo configuration"));
});

test("renaming a help evidence anchor fails even when the committed catalog digest is unchanged", t => {
  const root = modernSource(); t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const catalogFile = path.join(root, ".github/shared/help-catalog.json"), before = fs.readFileSync(catalogFile);
  const file = path.join(root, "docs/configuration.md");
  fs.writeFileSync(file, fs.readFileSync(file, "utf8").replace("## Strict Configuration Schema", "## Renamed Configuration Schema"));
  assert.throws(() => prepareHelp(root), /section|anchor|validation/);
  assert.deepEqual(fs.readFileSync(catalogFile), before);
});
