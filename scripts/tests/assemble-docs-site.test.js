"use strict";
// Created 2026-09-03.

const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const {
  cp,
  mkdtemp,
  mkdir,
  readFile,
  readdir,
  rm,
  symlink,
  writeFile,
} = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "scripts", "assemble-docs-site.js");
const node = process.execPath;

async function createSource(name) {
  const sourceRoot = await mkdtemp(path.join(os.tmpdir(), `cg-${name}-`));
  await mkdir(path.join(sourceRoot, "docs", "assets"), { recursive: true });
  await writeFile(path.join(sourceRoot, "docs", "index.html"), `<!doctype html><html><body><main>${name}</main></body></html>\n`);
  await writeFile(path.join(sourceRoot, "docs", "navigation.json"), JSON.stringify({ schemaVersion: "compound-gpid-docs-navigation-v1", groups: [] }) + "\n");
  await writeFile(path.join(sourceRoot, "docs", "assets", "site.css"), `body { color: ${name}; }\n`);
  await writeFile(path.join(sourceRoot, "docs", "assets", "site.js"), `document.title = ${JSON.stringify(name)};\n`);
  await writeFile(path.join(sourceRoot, "docs", ".nojekyll"), "\n");
  await writeFile(path.join(sourceRoot, "docs", `${name}.md`), `# ${name}\n\n<!-- Created 2026-09-03. -->\n`);
  await mkdir(path.join(sourceRoot, ".github"), { recursive: true });
  await writeFile(path.join(sourceRoot, ".github", `${name}.md`), `${name}\n`);
  return sourceRoot;
}

function run(args) {
  return spawnSync(node, [script, ...args], { encoding: "utf8" });
}

async function listFiles(directory) {
  const output = [];
  async function walk(current, prefix = "") {
    for (const entry of (await readdir(current, { withFileTypes: true })).sort((left, right) => left.name.localeCompare(right.name))) {
      const relative = path.join(prefix, entry.name);
      if (entry.isDirectory()) await walk(path.join(current, entry.name), relative);
      else output.push(relative.split(path.sep).join("/"));
    }
  }
  await walk(directory);
  return output;
}

async function removeTemporary(...directories) {
  await Promise.all(directories.map((directory) => rm(directory, { recursive: true, force: true })));
}

test("builds a deterministic combined root and dev site with provenance", async () => {
  const mainRoot = await createSource("main");
  const devRoot = await createSource("dev");
  const firstOutput = await mkdtemp(path.join(os.tmpdir(), "cg-site-first-"));
  const secondOutput = await mkdtemp(path.join(os.tmpdir(), "cg-site-second-"));
  try {
    const args = (output) => [
      "--main-root", mainRoot,
      "--dev-root", devRoot,
      "--out", output,
      "--main-sha", "1111111111111111111111111111111111111111",
      "--dev-sha", "2222222222222222222222222222222222222222",
    ];
    const first = run(args(firstOutput));
    assert.equal(first.status, 0, first.stderr + first.stdout);
    const second = run(args(secondOutput));
    assert.equal(second.status, 0, second.stderr + second.stdout);

    const firstSite = path.join(firstOutput, "site");
    const secondSite = path.join(secondOutput, "site");
    assert.deepEqual(await listFiles(firstSite), await listFiles(secondSite));
    for (const file of await listFiles(firstSite)) {
      assert.equal(await readFile(path.join(firstSite, file), "utf8"), await readFile(path.join(secondSite, file), "utf8"), file);
    }
    assert.match(await readFile(path.join(firstSite, "index.html"), "utf8"), /<main>main<\/main>/);
    assert.match(await readFile(path.join(firstSite, "dev", "index.html"), "utf8"), /development preview/i);
    assert.doesNotMatch(await readFile(path.join(firstSite, "index.html"), "utf8"), /development preview/i);

    const metadata = JSON.parse(await readFile(path.join(firstOutput, ".docs-build-metadata.json"), "utf8"));
    assert.equal(metadata.schemaVersion, 1);
    assert.equal(metadata.sources.main.branch, "main");
    assert.equal(metadata.sources.main.sha, "1111111111111111111111111111111111111111");
    assert.equal(metadata.sources.dev.branch, "dev");
    assert.equal(metadata.sources.dev.sha, "2222222222222222222222222222222222222222");
    assert.ok(metadata.sources.main.fingerprint);
    assert.ok(metadata.sources.dev.fingerprint);
    assert.ok(metadata.site.files["index.html"]);
    assert.ok(metadata.site.files["dev/index.html"]);
  } finally {
    await removeTemporary(mainRoot, devRoot, firstOutput, secondOutput);
  }
});

test("verifies complete artifact digests and rejects stale source inputs", async () => {
  const mainRoot = await createSource("main");
  const devRoot = await createSource("dev");
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-site-verify-"));
  try {
    const built = run([
      "--main-root", mainRoot,
      "--dev-root", devRoot,
      "--out", output,
      "--main-sha", "1111111111111111111111111111111111111111",
      "--dev-sha", "2222222222222222222222222222222222222222",
    ]);
    assert.equal(built.status, 0, built.stderr + built.stdout);
    const verified = run(["--verify", output, "--main-root", mainRoot, "--dev-root", devRoot]);
    assert.equal(verified.status, 0, verified.stderr + verified.stdout);

    await writeFile(path.join(devRoot, "docs", "dev.md"), "# changed\n");
    const stale = run(["--verify", output, "--main-root", mainRoot, "--dev-root", devRoot]);
    assert.notEqual(stale.status, 0);
    assert.match(stale.stderr + stale.stdout, /stale|fingerprint/i);

    await writeFile(path.join(output, "site", "index.html"), "tampered\n");
    const tampered = run(["--verify", output]);
    assert.notEqual(tampered.status, 0);
    assert.match(tampered.stderr + tampered.stdout, /digest|mismatch/i);
  } finally {
    await removeTemporary(mainRoot, devRoot, output);
  }
});

test("rejects output collisions and file-link entries at the filesystem boundary", async (t) => {
  const mainRoot = await createSource("main");
  const devRoot = await createSource("dev");
  const collisionOutput = await mkdtemp(path.join(os.tmpdir(), "cg-site-collision-"));
  const symlinkOutput = await mkdtemp(path.join(os.tmpdir(), "cg-site-symlink-"));
  try {
    await mkdir(path.join(mainRoot, "docs", "dev"), { recursive: true });
    await writeFile(path.join(mainRoot, "docs", "dev", "index.html"), "collision\n");
    const collision = run([
      "--main-root", mainRoot,
      "--dev-root", devRoot,
      "--out", collisionOutput,
      "--main-sha", "1111111111111111111111111111111111111111",
      "--dev-sha", "2222222222222222222222222222222222222222",
    ]);
    assert.notEqual(collision.status, 0);
    assert.match(collision.stderr + collision.stdout, /collision|overlap|dev/i);

    await rm(path.join(mainRoot, "docs", "dev"), { recursive: true, force: true });
    const outside = path.join(devRoot, "outside.txt");
    await writeFile(outside, "outside\n");
    try {
      try { await symlink(outside, path.join(devRoot, "docs", "outside.txt")); }
      catch (error) {
        if (process.platform !== "win32" || error.code !== "EPERM") throw error;
        // This restricted Windows token cannot create file symlinks. Exercise
        // the same real scanner with only the OS directory-entry type supplied.
        // Native hosts still execute the real file-symlink path above.
        t.diagnostic("Windows EPERM: portable file-link Dirent boundary, not native symlink qualification");
        await writeFile(path.join(devRoot, "docs", "outside.txt"), "must not copy");
        const fs = require("node:fs"), readdir = fs.readdirSync;
        t.mock.method(fs, "readdirSync", (directory, options) => {
          const rows = readdir(directory, options);
          if (directory !== path.join(devRoot, "docs") || !options?.withFileTypes) return rows;
          return rows.map(row => row.name !== "outside.txt" ? row : new Proxy(row, {
            get(target, key) { return key === "isSymbolicLink" ? () => true : Reflect.get(target, key); },
          }));
        });
      }
      const {writeCombinedSite} = require("../assemble-docs-site.js");
      assert.throws(() => writeCombinedSite({mainRoot, devRoot, out: symlinkOutput,
        mainSha: "1".repeat(40), devSha: "2".repeat(40)}), /symlink|symbolic/i);
      assert.deepEqual(await listFiles(symlinkOutput), []);
    } finally {
      await rm(outside, { force: true });
    }
  } finally {
    await removeTemporary(mainRoot, devRoot, collisionOutput, symlinkOutput);
  }
});

test("rejects incomplete source identity metadata", async () => {
  const mainRoot = await createSource("main");
  const devRoot = await createSource("dev");
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-site-metadata-"));
  try {
    const built = run([
      "--main-root", mainRoot,
      "--dev-root", devRoot,
      "--out", output,
      "--main-sha", "1111111111111111111111111111111111111111",
      "--dev-sha", "2222222222222222222222222222222222222222",
    ]);
    assert.equal(built.status, 0, built.stderr + built.stdout);
    const metadataPath = path.join(output, ".docs-build-metadata.json");
    const metadata = JSON.parse(await readFile(metadataPath, "utf8"));
    delete metadata.sources.dev.ref;
    await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
    const invalid = run(["--verify", output]);
    assert.notEqual(invalid.status, 0);
    assert.match(invalid.stderr + invalid.stdout, /invalid dev source record/i);
  } finally {
    await removeTemporary(mainRoot, devRoot, output);
  }
});

test("rejects self-consistent stable contamination at the source verifier boundary", async () => {
  const mainRoot = await createSource("main");
  const devRoot = await createSource("dev");
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-site-contamination-"));
  try {
    assert.equal(run(["--main-root", mainRoot, "--dev-root", devRoot, "--out", output,
      "--main-sha", "1".repeat(40), "--dev-sha", "2".repeat(40)]).status, 0);
    const poisoned = Buffer.from("<html><body>ATTACKER STABLE CONTENT</body></html>");
    await writeFile(path.join(output, "site/index.html"), poisoned);
    const metadataPath = path.join(output, ".docs-build-metadata.json");
    const metadata = JSON.parse(await readFile(metadataPath, "utf8"));
    metadata.site.files["index.html"] = require("node:crypto").createHash("sha256").update(poisoned).digest("hex");
    await writeFile(metadataPath, JSON.stringify(metadata));
    const result = run(["--verify", output, "--main-root", mainRoot, "--dev-root", devRoot]);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /stable.*(source|output|digest)/i);
  } finally {
    await removeTemporary(mainRoot, devRoot, output);
  }
});

test("reserves only the channel manifest output and preserves existing output on collision", async () => {
  const mainRoot = await createSource("main"), devRoot = await createSource("dev");
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-channels-reserved-"));
  try {
    await writeFile(path.join(output, "sentinel"), "previous valid artifact");
    for (const source of [mainRoot, devRoot]) {
      const collision = path.join(source, "docs/channels.json");
      await writeFile(collision, "{}");
      const result = run(["--main-root", mainRoot, "--dev-root", devRoot, "--out", output,
        "--main-sha", "1".repeat(40), "--dev-sha", "2".repeat(40)]);
      assert.equal(result.status, 1, result.stderr + result.stdout);
      assert.match(result.stderr, /reserved.*channels.json/);
      assert.equal(await readFile(path.join(output, "sentinel"), "utf8"), "previous valid artifact");
      await rm(collision);
    }
  } finally { await removeTemporary(mainRoot, devRoot, output); }
});

test("pairs the captured actual legacy root with the new dev runtime without rewriting root bytes", async () => {
  const mainRoot = await createSource("main"), devRoot = require("./docs-publishing-fixture.js").modernSource();
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-real-mixed-runtime-"));
  try {
    for (const sourceRoot of [mainRoot, devRoot]) {
      await rm(path.join(sourceRoot, "docs"), { recursive: true });
      await cp(path.join(root, "docs"), path.join(sourceRoot, "docs"), { recursive: true });
    }
    const legacy = path.join(__dirname, "fixtures/docs-redesign/legacy/docs");
    await cp(legacy, path.join(mainRoot, "docs"), { recursive: true });
    const legacyDocuments = require("./fixtures/docs-redesign/legacy-documents.json");
    for (const [file, text] of Object.entries(legacyDocuments)) await writeFile(path.join(mainRoot, "docs", file), text);
    await rm(path.join(mainRoot, "docs/assets/docs-contract.js"));
    const { digestTree } = require("../assemble-docs-site.js");
    const mainBefore = digestTree(path.join(mainRoot, "docs")), devBefore = digestTree(path.join(devRoot, "docs"));
    const result = run(["--main-root", mainRoot, "--dev-root", devRoot, "--out", output,
      "--main-sha", "1".repeat(40), "--dev-sha", "2".repeat(40)]);
    assert.equal(result.status, 0, result.stderr + result.stdout);
    const verified = run(["--verify", output, "--main-root", mainRoot, "--dev-root", devRoot]);
    assert.equal(verified.status, 0, verified.stderr + verified.stdout);
    assert.deepEqual(digestTree(path.join(mainRoot, "docs")), mainBefore);
    assert.deepEqual(digestTree(path.join(devRoot, "docs")), devBefore);
    assert.equal(await readFile(path.join(output, "site/assets/site.js"), "utf8"), await readFile(path.join(legacy, "assets/site.js"), "utf8"));
    assert.match(await readFile(path.join(output, "site/dev/assets/site.js"), "utf8"), /DocsContract.parseDocument/);
    assert.doesNotMatch(await readFile(path.join(output, "site/index.html"), "utf8"), /docs-contract\.js|dev-preview-banner/);
    assert.match(await readFile(path.join(output, "site/dev/index.html"), "utf8"), /assets\/docs-contract\.[a-f0-9]{64}\.js/);
  } finally { await removeTemporary(mainRoot, devRoot, output); }
});
