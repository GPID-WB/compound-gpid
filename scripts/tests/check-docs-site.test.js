"use strict";
// Created 2026-09-03.

const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { mkdtemp, mkdir, rm, cp, readFile, writeFile } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "scripts", "check-docs-site.js");
const node = process.execPath;
let source;

test.before(async () => {
  source = await mkdtemp(path.join(os.tmpdir(), "cg-pages-contract-"));
  for (const name of [".github", "docs", "README.md"]) {
    await cp(path.join(root, name), path.join(source, name), { recursive: true });
  }
  await mkdir(path.join(source, "scripts"));
  await cp(path.join(root, "scripts", "cg_skill.py"), path.join(source, "scripts", "cg_skill.py"));
});

test.after(async () => {
  await rm(source, { recursive: true, force: true });
});

test("accepts the unchanged real-source workflow fixture", () => {
  const result = spawnSync(node, [script, "--source-root", source], {
    cwd: root, encoding: "utf8", timeout: 30000,
  });
  assert.equal(result.status, 0, result.stderr + result.stdout);
});

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

const workflowVariants = [
  ["dev Pages permission", "pages.yml", "contents: read", "contents: read\n  pages: write", /pages.yml must remain unprivileged/],
  ["dev OIDC permission", "pages.yml", "contents: read", "contents: read\n  id-token: write", /pages.yml must remain unprivileged/],
  ["dev environment", "pages.yml", "    runs-on: ubuntu-latest", "    environment: github-pages\n    runs-on: ubuntu-latest", /pages.yml must remain unprivileged/],
  ["combined builder environment", "docs-site-build.yml", "    runs-on: ubuntu-latest", "    environment: github-pages\n    runs-on: ubuntu-latest", /docs-site-build.yml must remain unprivileged/],
  ["release builder environment", "release-docs.yml", "    runs-on: ubuntu-latest", "    environment: github-pages\n    runs-on: ubuntu-latest", /release-docs.yml must remain unprivileged/],
  ["mutable dev checkout", "pages.yml", "ref: ${{ github.sha }}", "ref: dev", /pages.yml must reference/],
  ["missing dev metadata", "pages.yml", "            .docs-build-metadata.json", "", /pages.yml must reference/],
  ["missing configure in dev controller", "release-pages.yml", "      - uses: actions/configure-pages@", "      - uses: example/not-configure@", /deploy-dev must reference actions\/configure-pages/],
  ["missing deploy in dev controller", "release-pages.yml", "      - uses: actions/deploy-pages@", "      - uses: example/not-deploy@", /deploy-dev must reference actions\/deploy-pages/],
  ["wrong exact-run artifact", "release-pages.yml", "artifact-ids: ${{ steps.authority.outputs.artifact_id }}", "name: latest-artifact", /deploy must reference artifact-ids/],
  ["missing exact dev run", "release-pages.yml", "run-id: ${{ github.event.workflow_run.id }}", "run-id: 1", /deploy-dev must reference run-id/],
  ["mutable controller", "release-pages.yml", "ref: ${{ github.sha }}", "ref: dev", /deploy must reference ref/],
  ["missing archive verification", "release-pages.yml", 'run: node scripts/legacy-pages.js archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"', "run: echo unchecked", /deploy must reference.*archive/],
  ["missing final dev cutover check", "release-pages.yml", "          node scripts/legacy-pages.js check\n          test", "          test", /deploy-dev must recheck authority after upload/],
  ["wrong combined upload", "release-pages.yml", "path: combined-artifact/site", "path: sources/dev/docs", /deploy-dev must reference path/],
  ["rebuild downloaded dev", "release-pages.yml", "node scripts/legacy-pages.js import-dev sources/dev dev-artifact", "node sources/dev/scripts/rebuild-docs.js --all", /must not execute mutable source or rebuild/],
  ["missing trusted dev import", "release-pages.yml", "node scripts/legacy-pages.js import-dev sources/dev dev-artifact", "echo unverified", /deploy-dev must reference.*import-dev/],
];

for (const [name, file, before, after, error] of workflowVariants) {
  test(`rejects split Pages workflow variant: ${name}`, async () => {
    const target = path.join(source, ".github", "workflows", file);
    const original = await readFile(target, "utf8");
    try {
      // Use real workflows and the actual validator process, not verifier mocks.
      assert.ok(original.includes(before), `variant anchor missing: ${name}`);
      await writeFile(target, original.replace(before, after));
      const result = spawnSync(node, [script, "--docs-root", path.join(source, "docs"), "--source-root", source], {
        cwd: root, encoding: "utf8", timeout: 30000,
      });
      assert.equal(result.status, 1, result.stderr + result.stdout);
      assert.match(result.stderr + result.stdout, error);
    } finally {
      await writeFile(target, original);
    }
  });
}
