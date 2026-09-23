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

test("hidden references remain registered, linked, and checked by the real validator", async () => {
  const target = path.join(source, "docs/navigation.json");
  const original = await readFile(target, "utf8");
  try {
    const manifest = JSON.parse(original);
    const skills = manifest.groups.find(group => group.pages.some(page => page.id === "skill-management"));
    skills.pages.forEach(page => { page.sidebar = false; });
    await writeFile(target, JSON.stringify(manifest));
    const result = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr + result.stdout);
    skills.pages.pop();
    await writeFile(target, JSON.stringify(manifest));
    const missing = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(missing.status, 1);
    assert.match(missing.stderr, /Navigation coverage failed/);
  } finally { await writeFile(target, original); }
});

test("split reading controls remain required and accessibility tokens cannot disappear", async () => {
  const htmlPath = path.join(source, "docs/index.html"), readingPath = path.join(source, "docs/assets/docs-reading.js");
  const html = await readFile(htmlPath, "utf8"), reading = await readFile(readingPath, "utf8");
  try {
    await writeFile(htmlPath, html.replace('<script src="assets/docs-reading.js"></script>', ""));
    const missing = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(missing.status, 1); assert.match(missing.stderr, /load reading controls/);
    await writeFile(htmlPath, html);
    await writeFile(readingPath, reading.replaceAll("aria-current", "removed-current"));
    const inaccessible = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(inaccessible.status, 1); assert.match(inaccessible.stderr, /missing contract: aria-current/);
  } finally { await writeFile(htmlPath, html); await writeFile(readingPath, reading); }
});

test("fenced examples cannot satisfy a real Markdown fragment link", async () => {
  const target = path.join(source, "docs/skills/management/security.md");
  const original = await readFile(target, "utf8");
  try {
    await writeFile(target, `${original}\n[Invalid](#fake-only-in-code)\n\n~~~md\n## Fake Only In Code\n~~~\n`);
    const result = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /missing fragment #fake-only-in-code/);
  } finally { await writeFile(target, original); }
});

test("the separate candidate-page allowance remains validated outside public navigation", async () => {
  const candidate = path.join(source, "docs/skills/management/phase1-candidate.md");
  const candidates = path.join(source, "docs/skills/management/candidates.json");
  let prior = null;
  try { prior = await readFile(candidates); } catch (error) { if (error.code !== "ENOENT") throw error; }
  try {
    await writeFile(candidate, "# Candidate\n\nNot in the sidebar.\n");
    await writeFile(candidates, JSON.stringify({ schemaVersion: "compound-gpid-docs-candidates-v1", pages: [
      { id: "phase1-candidate", title: "Candidate", description: "Candidate only", file: "docs/skills/management/phase1-candidate.md" },
    ] }));
    const allowed = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(allowed.status, 0, allowed.stderr + allowed.stdout);
    await writeFile(candidate, "# Candidate\n\n[Missing](missing-candidate.md)\n");
    const invalid = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(invalid.status, 1);
    assert.match(invalid.stderr, /targets missing/);
  } finally {
    await rm(candidate, { force: true });
    if (prior) await writeFile(candidates, prior); else await rm(candidates, { force: true });
  }
});

test("a heading inside a code fence cannot satisfy the page title requirement", async () => {
  const target = path.join(source, "docs/skills/management/security.md");
  const original = await readFile(target, "utf8");
  try {
    await writeFile(target, "```md\n# Not a Page Title\n```\n");
    const result = spawnSync(node, [script, "--source-root", source], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /must have a level-one heading/);
  } finally { await writeFile(target, original); }
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
  ["missing deploy in dev controller", "release-pages.yml", "      - name: Deploy development preview to GitHub Pages\n        uses: actions/deploy-pages@", "      - name: Deploy development preview to GitHub Pages\n        uses: example/not-deploy@", /deploy-dev must reference actions\/deploy-pages/],
  ["wrong exact-run artifact", "release-pages.yml", "artifact-ids: ${{ steps.authority.outputs.artifact_id }}", "name: latest-artifact", /deploy must reference artifact-ids/],
  ["missing exact dev run", "release-pages.yml", "run-id: ${{ github.event.workflow_run.id }}", "run-id: 1", /deploy-dev must reference run-id/],
  ["mutable controller", "release-pages.yml", "ref: ${{ github.sha }}\n          fetch-depth: 0\n          persist-credentials: false", "ref: dev\n          fetch-depth: 0\n          persist-credentials: false", /deploy must reference ref/],
  ["missing archive verification", "release-pages.yml", 'run: node scripts/legacy-pages.js archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"', "run: echo unchecked", /deploy must reference.*archive/],
  ["missing final dev cutover check", "release-pages.yml", "          node scripts/legacy-pages.js check\n          node scripts/legacy-pages.js recheck-official official-state.json\n          test \"$(gh api \"repos/$GITHUB_REPOSITORY/branches/dev\" --jq .commit.sha)\" = \"$DEV_SHA\"", "          echo skipped-recheck", /deploy-dev must recheck authority after upload/],
  ["wrong combined upload", "release-pages.yml", "path: combined-artifact/site", "path: sources/dev/docs", /deploy-dev must reference path/],
  ["rebuild downloaded dev", "release-pages.yml", "node scripts/legacy-pages.js import-dev sources/dev dev-artifact", "node sources/dev/scripts/rebuild-docs.js --all", /must not execute mutable source or rebuild/],
  ["missing trusted dev import", "release-pages.yml", "node scripts/legacy-pages.js import-dev sources/dev dev-artifact", "echo unverified", /deploy-dev must reference.*import-dev/],
  ["missing official restore", "release-pages.yml", "node scripts/legacy-pages.js restore-official official-source official-state.json", "echo unverified-restore", /deploy-dev must reference.*restore-official/],
  ["missing official seal on release deploy", "release-pages.yml", "node scripts/legacy-pages.js seal-official release-source release-artifact", "echo unsealed", /deploy must reference.*seal-official/],
  ["missing preview stamp", "release-pages.yml", "node scripts/legacy-pages.js stamp-preview official-state.json combined-artifact", "echo unstamped", /deploy-dev must reference.*stamp-preview/],
  ["missing official recheck", "release-pages.yml", "node scripts/legacy-pages.js recheck-official official-state.json", "echo unchecked-official", /deploy-dev must reference.*recheck-official/],
  ["stale main dev checkout", "release-pages.yml", "ref: ${{ steps.authority.outputs.release_sha }}\n          path: sources/dev", "ref: main\n          path: sources/dev", /never a moving main checkout/],
  ["wrong official composition root", "release-pages.yml", "--main-root official-source --dev-root sources/dev", "--main-root sources/main --dev-root sources/dev", /never a moving main checkout/],
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
