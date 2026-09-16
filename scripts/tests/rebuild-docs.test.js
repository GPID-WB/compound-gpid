"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { readFile, writeFile, mkdtemp, cp, rm } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "scripts", "rebuild-docs.js");
const fixtures = path.join(__dirname, "fixtures", "docs-automation", "src");
const node = process.execPath;

async function tempRepo(name) {
  const tmp = await mkdtemp(path.join(os.tmpdir(), "cg-docs-auto-"));
  await cp(path.join(fixtures, name), tmp, { recursive: true });
  return tmp;
}

function runRepo(dir, extraArgs = []) {
  return spawnSync(node, [script, "--root", dir, ...extraArgs], { encoding: "utf8" });
}

function expectedCommands() {
  return [
    "| Prompt | Model | Purpose |",
    "|--------|-------|---------|",
    "| `/cg-plan` | Copilot model picker | Create a plan. |",
    "| `/cg-work` | Copilot model picker | Run a plan step. |",
  ].join("\n");
}

function expectedResearchCommands() {
  return [
    "| Prompt | Model | Purpose |",
    "|--------|-------|---------|",
    "| `/cr-review` | Copilot model picker | Review research output with evidence, code, and methods. |",
  ].join("\n");
}

test("write mode updates only the marker interiors and preserves prose", async () => {
  const dir = await tempRepo("basic");
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const after = await readFile(path.join(dir, "docs", "reference.md"), "utf8");

  assert.match(after, new RegExp(`<!-- cg:auto:commands -->\\s*\\n${escapeRe(expectedCommands())}\\s*\\n<!-- cg:auto:end -->`));
  assert.match(after, new RegExp(`<!-- cg:auto:research-commands -->\\s*\\n${escapeRe(expectedResearchCommands())}\\s*\\n<!-- cg:auto:end -->`));
  assert.match(after, /^Prose that must be preserved byte-for-byte\.$/m);
  assert.match(after, /^These commands are owned by `suite-cr`\.$/m);

  // second run is deterministic
  const second = runRepo(dir);
  assert.equal(second.status, 0, second.stderr);
  const twice = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  assert.equal(twice, after);
});

test("--check reports stale with nonzero exit and does not write", async () => {
  const dir = await tempRepo("basic");
  const before = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  const result = runRepo(dir, ["--check"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /reference\.md/);
  const after = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  assert.equal(after, before, "--check must not mutate the file");
});

test("--check exits zero when current after a write", async () => {
  const dir = await tempRepo("basic");
  runRepo(dir);
  const result = runRepo(dir, ["--check"]);
  assert.equal(result.status, 0, result.stdout + result.stderr);
});

test("canonical prompt removal updates only the affected table", async () => {
  const dir = await tempRepo("basic");
  runRepo(dir); // establish current state
  await rm(path.join(dir, ".github", "prompts", "cg-work.prompt.md"));
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const after = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  assert.match(after, /\/cg-plan/);
  assert.doesNotMatch(after, /\/cg-work/);
  assert.match(after, /\/cr-review/);
});

test("missing close marker fails loudly without writing", async () => {
  const dir = await tempRepo("missing-close-marker");
  const before = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /marker|close|end/i);
  const after = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  assert.equal(after, before, "failed preflight must not write");
});

test("nested marker fails loudly", async () => {
  const dir = await tempRepo("nested-marker");
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /nested|duplicate|marker/i);
});

test("declared managed section without an owner fails", async () => {
  const dir = await tempRepo("unknown-section");
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /unknown-section|owner|managed section/i);
});

test("manifest page outside docs/ is rejected", async () => {
  const dir = await tempRepo("traversal");
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /outside|traversal|reject/i);
});

test("folded canonical descriptions are rendered completely and safely", async () => {
  const dir = await tempRepo("basic");
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const after = await readFile(path.join(dir, "docs", "reference.md"), "utf8");
  assert.match(after, /Review research output with evidence, code, and methods\./);
});

test("metadata fingerprint changes for canonical navigation input", async () => {
  const dir = await tempRepo("basic");
  const first = runRepo(dir, ["--all"]);
  assert.equal(first.status, 0, first.stderr + first.stdout);
  const metadataPath = path.join(dir, ".docs-build-metadata.json");
  const metadata = JSON.parse(await readFile(metadataPath, "utf8"));
  const navigationPath = path.join(dir, "docs", "navigation.json");
  await writeFile(navigationPath, `${await readFile(navigationPath, "utf8")}\n`);
  const verify = runRepo(dir, ["--verify-fingerprint", metadataPath]);
  assert.notEqual(verify.status, 0);
  assert.match(verify.stdout + verify.stderr, /stale/i);
});

test("complete --check reports stale release notes without writing", async () => {
  const dir = await tempRepo("basic");
  await cp(path.join(fixtures, "releases-multi", "releases"), path.join(dir, "releases"), { recursive: true });
  const before = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  const result = runRepo(dir, ["--all", "--check"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /whats-new\.md/);
  assert.equal(await readFile(path.join(dir, "docs", "whats-new.md"), "utf8"), before);
});

test("marker-like examples in fenced code do not affect managed regions", async () => {
  const dir = await tempRepo("basic");
  const refPath = path.join(dir, "docs", "reference.md");
  await writeFile(refPath, `${await readFile(refPath, "utf8")}\n\`\`\`html\n<!-- cg:auto:end -->\n\`\`\`\n`);
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const after = await readFile(refPath, "utf8");
  assert.match(after, /```html\n<!-- cg:auto:end -->\n```/);
});

function escapeRe(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
