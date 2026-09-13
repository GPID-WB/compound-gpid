"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const snapshots = require("../docs-snapshots.js");
const crypto = require("node:crypto");
const corpus = require("./fixtures/snapshot-paths.json");

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "cg-snapshot-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const name of ["release", "stable", "dev"]) {
    fs.mkdirSync(path.join(root, name, "docs/assets"), { recursive: true });
    for (const file of ["index.html", "navigation.json", "assets/site.css", "assets/site.js", ".nojekyll"])
      fs.writeFileSync(path.join(root, name, "docs", file), file === "index.html" ? `<body>${name}</body>` : name);
  }
  return root;
}

function build(root, name, tag, sha) {
  return snapshots.buildSnapshot({ root: path.join(root, name), out: path.join(root, `${name}-snapshot`),
    kind: name === "dev" ? "dev" : "release", tag, sha, runId: name === "dev" ? 2 : 1, runAttempt: 1 });
}

test("dev advancement changes only composition, never immutable release identity", t => {
  const root = fixture(t);
  const release = build(root, "release", "v1.5.0-rc.10", "a".repeat(40));
  build(root, "stable", "v2.0.0", "b".repeat(40));
  build(root, "dev", null, "c".repeat(40));
  const options = { releases: [path.join(root, "release-snapshot"), path.join(root, "stable-snapshot")],
    dev: path.join(root, "dev-snapshot"), out: path.join(root, "site"), composerRevision: "d".repeat(40),
    currentDevSha: "c".repeat(40), stableTag: "v2.0.0" };
  const first = snapshots.composeSnapshots(options);
  assert.equal(first.stableTag, "v2.0.0");
  assert.equal(fs.readFileSync(path.join(root, "site/site/index.html"), "utf8"), "<body>stable</body>");
  assert.equal(fs.readFileSync(path.join(root, "site/site/releases/v1.5.0-rc.10/index.html"), "utf8"), "<body>release</body>");
  fs.rmSync(path.join(root, "dev-snapshot"), { recursive: true });
  build(root, "dev", null, "e".repeat(40));
  assert.throws(() => snapshots.composeSnapshots({ ...options, out: path.join(root, "stale") }), /dev.*stale/i);
  const second = snapshots.composeSnapshots({ ...options, out: path.join(root, "retry"), currentDevSha: "e".repeat(40) });
  assert.notDeepEqual(first.dev, second.dev);
  assert.deepEqual(snapshots.verifySnapshot(path.join(root, "release-snapshot")), release);
  assert.throws(() => snapshots.composeSnapshots({ ...options, stableTag: "v1.5.0-rc.10", out: path.join(root, "wrong") }), /stable/i);
});

test("snapshot inventory and reserved path boundaries fail closed", t => {
  const root = fixture(t);
  build(root, "release", "v1.0.0", "a".repeat(40));
  fs.writeFileSync(path.join(root, "release-snapshot/site/index.html"), "tampered");
  assert.throws(() => snapshots.verifySnapshot(path.join(root, "release-snapshot")), /inventory/i);
  fs.mkdirSync(path.join(root, "dev/docs/dev"));
  fs.writeFileSync(path.join(root, "dev/docs/dev/index.html"), "collision");
  assert.throws(() => build(root, "dev", null, "b".repeat(40)), /reserved/i);
  assert.throws(() => snapshots.buildSnapshot({ root: path.join(root, "stable"), out: path.join(root, "bad"),
    kind: "release", tag: "../dev", sha: "a".repeat(40), runId: 1, runAttempt: 1 }), /tag/i);
});

test("prototype aliases, directory depth and root links are rejected", t => {
  const root = fixture(t);
  fs.writeFileSync(path.join(root, "release/docs/__proto__"), "not omitted");
  assert.throws(() => build(root, "release", "v1.0.0", "a".repeat(40)), /path|alias/i);
  let deep = path.join(root, "dev/docs");
  for (let i = 0; i < 34; i++) { deep = path.join(deep, "d"); fs.mkdirSync(deep); }
  assert.throws(() => build(root, "dev", null, "a".repeat(40)), /limit/i);
  fs.symlinkSync(path.join(root, "stable"), path.join(root, "link"), process.platform === "win32" ? "junction" : "dir");
  assert.throws(() => snapshots.buildSnapshot({root: path.join(root, "link"), out: path.join(root, "out"),
    kind: "release", tag: "v1.0.0", sha: "a".repeat(40), runId: 1, runAttempt: 1}), /link/i);
});

test("composition verification rejects tampering and omitted release selection", t => {
  const root = fixture(t);
  build(root, "stable", "v2.0.0", "b".repeat(40));
  build(root, "dev", null, "c".repeat(40));
  const options = {releases: [path.join(root, "stable-snapshot")], dev: path.join(root, "dev-snapshot"),
    out: path.join(root, "composition"), composerRevision: "d".repeat(40), currentDevSha: "c".repeat(40), stableTag: "v2.0.0"};
  const record = snapshots.composeSnapshots(options);
  assert.deepEqual(snapshots.verifyComposition(options.out, record), record);
  fs.writeFileSync(path.join(options.out, "site/index.html"), "tampered");
  assert.throws(() => snapshots.verifyComposition(options.out, record), /inventory/i);
});

test("snapshot envelope round trips with exact bytes and rejects path injection", t => {
  const root = fixture(t);
  const expected = build(root, "stable", "v2.0.0", "a".repeat(40));
  const file = path.join(root, "snapshot.json");
  snapshots.exportSnapshot(path.join(root, "stable-snapshot"), file);
  assert.deepEqual(snapshots.importSnapshot(file, path.join(root, "restored")), expected);
  const payload = JSON.parse(fs.readFileSync(file, "utf8"));
  payload.files["../escape"] = Buffer.from("escape").toString("base64");
  payload.record.files["../escape"] = "0".repeat(64);
  fs.writeFileSync(file, JSON.stringify(payload));
  assert.throws(() => snapshots.importSnapshot(file, path.join(root, "invalid")), /path/i);
  assert.equal(fs.existsSync(path.join(root, "escape")), false);
});

for (const item of corpus) test(`shared snapshot path corpus: ${item.paths.join(",")}`, t => {
  const root = fixture(t);
  const record = build(root, "stable", "v1.0.0", "a".repeat(40));
  const file = path.join(root, "snapshot.json");
  snapshots.exportSnapshot(path.join(root, "stable-snapshot"), file);
  const envelope = JSON.parse(fs.readFileSync(file, "utf8"));
  for (const name of item.paths) {
    envelope.files[name] = "eA==";
    record.files[name] = crypto.createHash("sha256").update("x").digest("hex");
  }
  const { snapshotDigest, ...identity } = record;
  identity.files = Object.fromEntries(Object.entries(identity.files).sort());
  record.snapshotDigest = crypto.createHash("sha256").update(JSON.stringify(identity)).digest("hex");
  envelope.record = record;
  fs.writeFileSync(file, JSON.stringify(envelope));
  const out = path.join(root, "restored");
  if (item.valid) assert.deepEqual(snapshots.importSnapshot(file, out), record);
  else {
    assert.throws(() => snapshots.importSnapshot(file, out));
    assert.equal(fs.existsSync(out), false, "Invalid approved data must fail before any materialization");
  }
});

test("composition capacity is rejected before copying any output", t => {
  const root = fixture(t);
  for (let n = 0; n < 4995; n++) fs.writeFileSync(path.join(root, "stable/docs", `f${n}`), "x");
  build(root, "stable", "v2.0.0", "a".repeat(40));
  build(root, "dev", null, "b".repeat(40));
  const out = path.join(root, "too-large");
  assert.throws(() => snapshots.composeSnapshots({ releases: [path.join(root, "stable-snapshot")],
    dev: path.join(root, "dev-snapshot"), out, composerRevision: "c".repeat(40),
    currentDevSha: "b".repeat(40), stableTag: "v2.0.0" }), /limit|capacity/i);
  assert.equal(fs.existsSync(out), false);
});

test("snapshot canonical identity is independent of JSON object key order", t => {
  const root = fixture(t);
  const record = build(root, "stable", "v1.0.0", "a".repeat(40));
  const file = path.join(root, "snapshot.json");
  snapshots.exportSnapshot(path.join(root, "stable-snapshot"), file);
  const envelope = JSON.parse(fs.readFileSync(file, "utf8"));
  envelope.record = Object.fromEntries(Object.entries(envelope.record).reverse());
  envelope.record.files = Object.fromEntries(Object.entries(envelope.record.files).reverse());
  envelope.files = Object.fromEntries(Object.entries(envelope.files).reverse());
  fs.writeFileSync(file, JSON.stringify(envelope));
  assert.equal(snapshots.importSnapshot(file, path.join(root, "restored")).snapshotDigest, record.snapshotDigest);
});

for (const kind of ["duplicate", "bom"]) test(`strict snapshot JSON rejects ${kind} before output`, t => {
  const root = fixture(t);
  build(root, "stable", "v1.0.0", "a".repeat(40));
  const file = path.join(root, "snapshot.json");
  snapshots.exportSnapshot(path.join(root, "stable-snapshot"), file);
  let text = fs.readFileSync(file, "utf8");
  text = kind === "bom" ? "\ufeff" + text : text.replace('"schemaVersion":2', '"schemaVersion":2,"schemaVersion":2');
  fs.writeFileSync(file, text);
  assert.throws(() => snapshots.importSnapshot(file, path.join(root, "invalid")));
  assert.equal(fs.existsSync(path.join(root, "invalid")), false);
});
