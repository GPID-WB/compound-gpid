"use strict";
// Created 2026-09-03.

const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { mkdtemp, rm } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "scripts", "check-docs-site.js");
const node = process.execPath;

test("validates a docs tree against an explicitly supplied source root", async () => {
  const workingDirectory = await mkdtemp(path.join(os.tmpdir(), "cg-docs-check-"));
  try {
    const result = spawnSync(node, [
      script,
      "--docs-root", path.join(root, "docs"),
      "--source-root", root,
    ], { cwd: workingDirectory, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr + result.stdout);
  } finally {
    await rm(workingDirectory, { recursive: true, force: true });
  }
});

test("rejects unknown validation arguments", () => {
  const result = spawnSync(node, [script, "--not-a-real-option"], { cwd: root, encoding: "utf8" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr + result.stdout, /Usage|unknown|argument/i);
});
