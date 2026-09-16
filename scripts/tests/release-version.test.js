"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const corpus = require("../../packages/cg-release/tests/fixtures/versions.json");
const { parseReleaseTag, compareReleaseTags } = require("../release-version.js");
const { legacyDocsBranch } = require("../release-version.js");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { loadReleasePayloads } = require("../generate-whats-new.js");

test("strict SemVer corpus, ASCII numeric order, and build identity", () => {
  for (const value of corpus.valid) assert.doesNotThrow(() => parseReleaseTag(`v${value}`));
  for (const value of corpus.invalid) assert.throws(() => parseReleaseTag(`v${value}`));
  const ascending = corpus.ascending.map(v => `v${v}`);
  assert.deepEqual([...ascending].reverse().sort(compareReleaseTags), ascending);
  for (const [a, b] of corpus.equivalent) assert.equal(compareReleaseTags(`v${a}`, `v${b}`), 0);
  assert.equal(compareReleaseTags("v1.5.0-rc.2", "v1.5.0-rc.10"), -1);
  assert.equal(compareReleaseTags("v1.5.0.9000", "v1.5.0.9001"), -1);
  assert.equal(parseReleaseTag("v1.5.0.9000").legacy, true);
});

test("legacy docs guards parse all reader identities but reject controller ownership", () => {
  assert.equal(legacyDocsBranch("v1.0.0"), "main");
  assert.equal(legacyDocsBranch("v1.0.0.9000"), "dev");
  assert.throws(() => legacyDocsBranch("v1.1.0-rc.10"), /controller/i);
  assert.throws(() => legacyDocsBranch("v1.0.0+build-x"), /controller/i);
  assert.throws(() => legacyDocsBranch("v1.0.0", {tag: "v1.0.0"}), /controller/i);
  assert.throws(() => legacyDocsBranch("v01.0.0"), /tag/i);
});

test("complete payload loader accepts SemVer filenames and preserves exact latest bytes", t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "cg-payload-reader-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, "releases"));
  const tag = "v1.5.0-rc.10+build.2";
  const payload = { schemaVersion: 1, tag, publishedAt: "2026-09-12T00:00:00Z", releaseDate: "2026-09-12",
    name: tag, url: `https://github.com/GPID-WB/compound-gpid/releases/tag/${tag}`, sourceUrl: `https://github.com/GPID-WB/compound-gpid/tree/${tag}`,
    sections: [{kind: "internal", title: "Reviewed changes", entries: ["Exact bytes"]}] };
  const raw = JSON.stringify(payload) + "\n";
  fs.writeFileSync(path.join(root, "releases", tag + ".json"), raw);
  fs.writeFileSync(path.join(root, "releases/latest.json"), raw);
  assert.deepEqual(loadReleasePayloads(root)[0].raw, Buffer.from(raw));
  fs.appendFileSync(path.join(root, "releases/latest.json"), "\n");
  const result = require("node:child_process").spawnSync(process.execPath,
    [path.resolve(__dirname, "../generate-whats-new.js"), "--root", root, "--validate-release-set"], {encoding: "utf8"});
  assert.equal(result.status, 1);
  assert.match(result.stderr, /byte-match/);
});
