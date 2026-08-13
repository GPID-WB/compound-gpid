"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { readFile, writeFile, mkdtemp, cp, rm } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "scripts", "generate-whats-new.js");
const fixtures = path.join(__dirname, "fixtures", "docs-automation", "src");
const node = process.execPath;

async function tempRepo(name) {
  const tmp = await mkdtemp(path.join(os.tmpdir(), "cg-whatsnew-"));
  await cp(path.join(fixtures, name), tmp, { recursive: true });
  return tmp;
}

function runRepo(dir, extraArgs = []) {
  return spawnSync(node, [script, "--root", dir, ...extraArgs], { encoding: "utf8" });
}

test("write mode renders two immutable releases exactly once each", async () => {
  const dir = await tempRepo("releases-multi");
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const page = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");

  const count = (re) => (page.match(re) || []).length;
  assert.equal(count(/### v0\.2\.0/g), 1);
  assert.equal(count(/### v0\.1\.0/g), 1);
  assert.ok(count(/### v0\.[0-9.]+/g) >= 2, "renders every versioned payload");

  // newest first
  assert.ok(page.indexOf("v0.2.0") < page.indexOf("v0.1.0"));
  assert.match(page, /\[View source tag\]\(https:\/\/github\.com\/GPID-WB\/compound-gpid\/tree\/v0\.2\.0\)/);

  // latest.json is not rendered as a second release
  assert.ok(!/### v0\.2\.0[^\n]*\n[^\n]*\n[^\n]*### v0\.2\.0/.test(page));

  // marker pair preserved
  assert.match(page, /<!-- cg:auto:release-notes -->/);
  assert.match(page, /<!-- cg:auto:end -->/);
});

test("payload text with pipes and line breaks is escaped", async () => {
  const dir = await tempRepo("releases-multi");
  runRepo(dir);
  const page = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  assert.match(page, /a \\\| pipe/);
  assert.doesNotMatch(page, /\n\nAdded a thing with a \\\| pipe and a line\nbreak/);
});

test("--check reports stale with nonzero exit and does not write", async () => {
  const dir = await tempRepo("releases-multi");
  const before = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  const result = runRepo(dir, ["--check"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /whats-new\.md/);
  const after = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  assert.equal(after, before);
});

test("--check exits zero when current after a write", async () => {
  const dir = await tempRepo("releases-multi");
  runRepo(dir);
  const result = runRepo(dir, ["--check"]);
  assert.equal(result.status, 0, result.stdout + result.stderr);
});

test("empty release directory renders a deterministic empty state", async () => {
  const dir = await tempRepo("releases-empty");
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const page = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  assert.match(page, /No releases/);
  assert.match(page, /<!-- cg:auto:release-notes -->/);
  assert.match(page, /<!-- cg:auto:end -->/);

  // and the empty state is considered current
  const check = runRepo(dir, ["--check"]);
  assert.equal(check.status, 0, check.stdout + check.stderr);
});

test("--validate-payload accepts a valid payload", async () => {
  const dir = await tempRepo("releases-multi");
  const result = runRepo(dir, ["--validate-payload", "releases/v0.2.0.json"]);
  assert.equal(result.status, 0, result.stdout + result.stderr);
});

test("--validate-payload rejects an unknown kind", async () => {
  const dir = await tempRepo("unknown-kind");
  const result = runRepo(dir, ["--validate-payload", "releases/v0.1.0.json"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /kind|mystery|invalid/i);
});

test("invalid latest.json fails before rendering", async () => {
  const dir = await tempRepo("releases-multi");
  // corrupt latest.json so it no longer matches the versioned payload
  await writeFile(
    path.join(dir, "releases", "latest.json"),
    JSON.stringify({ schemaVersion: 1, tag: "v9.9.9", publishedAt: "2026-09-01T00:00:00Z", name: "Ghost", url: "https://github.com/GPID-WB/compound-gpid/releases/tag/v9.9.9", sourceUrl: "https://github.com/GPID-WB/compound-gpid/tree/v9.9.9", sections: [{ kind: "new", title: "X", entries: ["Y"] }] })
  );
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /latest|duplicate|mismatch|invalid/i);
});

test("payload URL must match its immutable tag", async () => {
  const dir = await tempRepo("releases-multi");
  const payloadPath = path.join(dir, "releases", "v0.2.0.json");
  const payload = JSON.parse(await readFile(payloadPath, "utf8"));
  payload.sourceUrl = "https://github.com/example/repo/tree/v0.1.0";
  await writeFile(payloadPath, JSON.stringify(payload));
  const result = runRepo(dir, ["--validate-payload", "releases/v0.2.0.json"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /sourceUrl|tag/i);
});

test("history is capped at twenty releases with an older-history link", async () => {
  const dir = await tempRepo("releases-multi");
  await rm(path.join(dir, "releases", "latest.json"));
  const releasesDir = path.join(dir, "releases");
  for (let i = 3; i <= 22; i++) {
    const tag = `v1.0.${i}`;
    const payload = {
      schemaVersion: 1,
      tag,
      publishedAt: `2026-08-${String(i - 2).padStart(2, "0")}T12:00:00Z`,
      name: `Release ${i}`,
      url: `https://github.com/GPID-WB/compound-gpid/releases/tag/${tag}`,
      sourceUrl: `https://github.com/GPID-WB/compound-gpid/tree/${tag}`,
      sections: [{ kind: "internal", title: "Maintenance", entries: ["Updated tooling"] }],
    };
    await writeFile(path.join(releasesDir, `${tag}.json`), JSON.stringify(payload));
  }
  const result = runRepo(dir);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const page = await readFile(path.join(dir, "docs", "whats-new.md"), "utf8");
  assert.equal((page.match(/^### v/gm) || []).length, 20);
  assert.match(page, /\[View older releases\]\(https:\/\/github\.com\/GPID-WB\/compound-gpid\/releases\)/);
});

test("payload URLs must target the Compound GPID repository", async () => {
  const dir = await tempRepo("releases-multi");
  const payloadPath = path.join(dir, "releases", "v0.2.0.json");
  const payload = JSON.parse(await readFile(payloadPath, "utf8"));
  payload.url = "https://github.com/example/repo/releases/tag/v0.2.0";
  await writeFile(payloadPath, JSON.stringify(payload));
  const result = runRepo(dir, ["--validate-payload", "releases/v0.2.0.json"]);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /GitHub release URL/i);
});

test("latest.json must match the newest immutable release", async () => {
  const dir = await tempRepo("releases-multi");
  await writeFile(
    path.join(dir, "releases", "latest.json"),
    await readFile(path.join(dir, "releases", "v0.1.0.json"), "utf8")
  );
  const result = runRepo(dir);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout + result.stderr, /latest\.json.*newest/i);
});
