"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { test } = require("node:test");

const root = path.resolve(__dirname, "..", "..", "..");
const workflow = fs.readFileSync(path.join(root, ".github/workflows/release-pages.yml"), "utf8")
  .replace(/\r\n/g, "\n");
// Execute the controller's actual Node heredoc, not a copy of its verification logic.
const verifier = workflow.match(/node - "\$RELEASE_TAG" <<'NODE'\n([\s\S]*?)\n          NODE\n/)[1]
  .replace(/^          /gm, "");
const uploadPath = workflow.match(/name: Upload verified release Pages artifact[\s\S]*?path: ([^\n]+)/)[1];

/** Create a minimal combined-site artifact and run the controller against it. */
function fixture(t, tag = "v1.2.3.4") {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "release-pages-test-"));
  t.after(() => fs.rmSync(cwd, { recursive: true, force: true }));
  const artifact = path.join(cwd, "release-artifact");
  const site = path.join(artifact, "site");
  fs.mkdirSync(path.join(site, "dev"), { recursive: true });
  const files = {
    "index.html": "<html><body>Release</body></html>",
    "dev/index.html": "<html><body>Development preview</body></html>",
    ".nojekyll": "",
  };
  const digests = {};
  for (const [name, content] of Object.entries(files)) {
    fs.writeFileSync(path.join(site, name), content);
    digests[name] = crypto.createHash("sha256").update(content).digest("hex");
  }
  const metadataPath = path.join(artifact, ".docs-build-metadata.json");
  const metadata = { schemaVersion: 1, site: { files: digests } };
  fs.writeFileSync(metadataPath, JSON.stringify(metadata));
  const releases = path.join(cwd, "release-validation", "releases");
  fs.mkdirSync(releases, { recursive: true });
  const payloadPath = path.join(releases, `${tag}.json`);
  fs.writeFileSync(payloadPath, JSON.stringify({ tag, schemaVersion: 1, sections: [{}] }));
  return {
    cwd, artifact, site, metadataPath, payloadPath,
    run: () => spawnSync(process.execPath, ["-", tag], {
      cwd, input: verifier, encoding: "utf8", timeout: 10000,
    }),
  };
}

for (const tag of ["v1.2.3", "v1.2.3.4"]) {
  test(`verifies the combined site and selects it for upload for ${tag}`, (t) => {
    const f = fixture(t, tag);
    assert.equal(fs.existsSync(path.join(f.artifact, "docs")), false);
    const result = f.run();
    assert.equal(result.status, 0, result.stderr);
    assert.equal(path.resolve(f.cwd, uploadPath), f.site);
    assert.equal(fs.existsSync(path.join(f.cwd, uploadPath, "dev/index.html")), true);
  });
}

test("rejects a missing site even when the old docs directory exists", (t) => {
  const f = fixture(t);
  fs.renameSync(f.site, path.join(f.artifact, "docs"));
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /ENOENT.*release-artifact[\\/]site/);
});

test("rejects changed site bytes", (t) => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.site, "dev/index.html"), "changed");
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Artifact digest mismatch: dev\/index.html/);
});

for (const change of ["missing", "extra"]) {
  test(`rejects ${change} site files`, (t) => {
    const f = fixture(t);
    if (change === "missing") fs.unlinkSync(path.join(f.site, ".nojekyll"));
    else fs.writeFileSync(path.join(f.site, "extra.html"), "extra");
    const result = f.run();
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /Artifact file list mismatch/);
  });
}

for (const metadata of [{ schemaVersion: 2, site: { files: {} } }, { schemaVersion: 1 }]) {
  test(`rejects invalid build metadata ${JSON.stringify(metadata)}`, (t) => {
    const f = fixture(t);
    fs.writeFileSync(f.metadataPath, JSON.stringify(metadata));
    const result = f.run();
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /Invalid documentation build metadata/);
  });
}

test("requires the build metadata file", (t) => {
  const f = fixture(t);
  fs.unlinkSync(f.metadataPath);
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /ENOENT.*\.docs-build-metadata\.json/);
});

for (const payload of [
  { tag: "v9.9.9", schemaVersion: 1, sections: [{}] },
  { tag: "v1.2.3.4", schemaVersion: 2, sections: [{}] },
  { tag: "v1.2.3.4", schemaVersion: 1, sections: [] },
]) {
  test(`rejects invalid release payload ${JSON.stringify(payload)}`, (t) => {
    const f = fixture(t);
    fs.writeFileSync(f.payloadPath, JSON.stringify(payload));
    const result = f.run();
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /Invalid durable release payload/);
  });
}

test("rejects symbolic links inside the site", (t) => {
  const f = fixture(t);
  fs.symlinkSync(path.join(f.site, "dev"), path.join(f.site, "linked"),
    process.platform === "win32" ? "junction" : "dir");
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Artifact contains symbolic link/);
});

test("retains the protected controller, exact build identity, lineage, and newest-release gates", () => {
  for (const guard of [
    'workflows: ["Build release documentation"]',
    "if: github.event.workflow_run.conclusion == 'success'",
    "name: github-pages",
    "ref: main",
    "name: release-docs-site",
    "run-id: ${{ github.event.workflow_run.id }}",
    "RELEASE_TAG: ${{ github.event.workflow_run.head_branch }}",
    "RELEASE_SHA: ${{ github.event.workflow_run.head_sha }}",
    'required_branch="main"',
    'if [[ "$RELEASE_TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$ ]]; then\n            required_branch="dev"',
    'elif [[ ! "$RELEASE_TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]; then',
    'test "$(git rev-list -n 1 "$RELEASE_TAG")" = "$RELEASE_SHA"',
    'git merge-base --is-ancestor "$RELEASE_SHA" "origin/$required_branch"',
    'if [ "$required_branch" = "dev" ]; then\n            git merge-base --is-ancestor origin/main "$RELEASE_SHA"',
    'cmp -s "release-validation/releases/$RELEASE_TAG.json" release-validation/releases/latest.json',
    'cmp -s "release-validation/releases/$RELEASE_TAG.json" release-validation/current-latest.json',
    'git fetch origin "$RELEASE_BRANCH"',
    "cmp -s release-validation/releases/latest.json release-validation/recheck-latest.json",
  ]) assert.ok(workflow.includes(guard), `Missing guard: ${guard}`);
  assert.ok(workflow.indexOf("name: Recheck release is still newest")
    < workflow.indexOf("name: Deploy to GitHub Pages"));
});
