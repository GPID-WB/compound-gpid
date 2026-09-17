"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const crypto = require("node:crypto");
const build = () => require("../docs-build-contract.js");
const fixture = path.join(__dirname, "fixtures/docs-redesign");
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");

test("producer selection is explicit and never tries a weaker fallback", () => {
  const { selectProducer, producers } = build();
  assert.equal(selectProducer({ producerContract: "compound-gpid-docs-producer-v2", fingerprintVersion: 2 }, "compound-gpid-docs-producer-v2"), producers["compound-gpid-docs-producer-v2"]);
  assert.throws(() => selectProducer({ producerContract: "compound-gpid-docs-producer-v1", fingerprintVersion: 1 }, "compound-gpid-docs-producer-v2"), /downgrade|canonical/);
  assert.throws(() => selectProducer({ producerContract: "unknown", fingerprintVersion: 2 }, "unknown"), /unknown/);
  assert.throws(() => selectProducer({ producerContract: "compound-gpid-docs-producer-v2", fingerprintVersion: 1 }, "compound-gpid-docs-producer-v2"), /fingerprint/);
  assert.throws(() => selectProducer({ producerContract: "compound-gpid-docs-producer-v2", fingerprintVersion: 2 }, "compound-gpid-docs-producer-v2", ["compound-gpid-docs-producer-v1"]), /unsupported/);
});

test("versionless metadata is legacy only for its exact recognized producer shape", () => {
  const { selectProducer } = build();
  const old = { schemaVersion: 1, version: "1", site: { fingerprint: "b".repeat(64), files: { "index.html": "c".repeat(64) } } };
  assert.equal(selectProducer(old, "compound-gpid-docs-producer-v1").fingerprintVersion, 1);
  assert.throws(() => selectProducer(old, "compound-gpid-docs-producer-v2"), /canonical|downgrade/);
  assert.throws(() => selectProducer({ ...old, fingerprintVersion: 1 }, "compound-gpid-docs-producer-v1"), /version/);
  assert.throws(() => selectProducer({ ...old, surprise: true }, "compound-gpid-docs-producer-v1"), /shape/);
});

function channel(name, legacy) {
  const version = legacy ? 1 : 2;
  const row = { path: name === "published" ? "" : "dev/", source: { sha: "a".repeat(40), branch: name === "published" ? "main" : "dev", ref: name === "published" ? "main" : "dev" },
    producerContract: `compound-gpid-docs-producer-v${version}`, fingerprintVersion: version, fingerprint: "b".repeat(64),
    runtimeContract: `compound-gpid-docs-runtime-v${version}`, headingContract: `compound-gpid-headings-v${version}`,
    capabilities: { sectionLinks: true, redirectMappings: !legacy, switchNotices: !legacy, reverseSwitching: !legacy, verifiedIdentity: !legacy },
    files: { "index.html": "c".repeat(64), "navigation.json": "d".repeat(64), "guide.md": "e".repeat(64), "assets/site.js": "f".repeat(64), "assets/site.css": "1".repeat(64), ".nojekyll": "2".repeat(64) },
    shellBuildId: null, assets: [] };
  if (!legacy) {
    row.files["assets/docs-contract.js"] = hash("canonical helper");
    row.shellBuildId = build().shellBuildId(row);
    for (const source of build().assetSources(version)) {
      const sha256 = hash(source);
      const output = source.replace(/\.(js|css)$/, `.${sha256}.$1`);
      row.files[output] = sha256;
      row.assets.push({ source, path: output, sha256, integrity: `sha256-${Buffer.from(sha256, "hex").toString("base64")}` });
    }
  }
  return row;
}

test("channel shape supports legacy root and upgraded dev without inventing legacy controls", () => {
  const data = { schemaVersion: "compound-gpid-docs-channels-v1", channels: { published: channel("published", true), development: channel("development", false) } };
  build().validateChannels(data);
  const bad = structuredClone(data);
  bad.channels.published.capabilities.verifiedIdentity = true;
  assert.throws(() => build().validateChannels(bad), /capabilit/);
  for (const mutate of [
    value => { value.channels.archive = value.channels.published; },
    value => { value.channels.development.path = "../dev/"; },
    value => { value.channels.development.runtimeContract = "unknown"; },
    value => { value.channels.development.files["channels.json"] = "a".repeat(64); },
    value => { value.channels.development.files["../secret"] = "a".repeat(64); },
    value => { value.channels.development.files["dev/leak.md"] = "a".repeat(64); },
    value => { value.channels.development.shellBuildId = "0".repeat(64); },
    value => { value.channels.development.assets[0].integrity = "sha256-wrong"; },
    value => { value.channels.development.assets.pop(); },
    value => { value.channels.development.source.sha = "short"; },
    value => { value.channels.development.files["guide.md"] = "invalid"; },
    value => { delete value.channels.published.files["index.html"]; },
  ]) {
    const invalid = structuredClone(data); mutate(invalid);
    assert.throws(() => build().validateChannels(invalid));
  }
});

test("exact reserved paths do not exempt arbitrary JSON or generated directories", () => {
  const { assertSourcePaths, transforms } = build();
  assert.throws(() => assertSourcePaths(["channels.json"]), /reserved/);
  assert.throws(() => assertSourcePaths(["Channels.json"]), /reserved/);
  assert.throws(() => assertSourcePaths(["assets/site." + "a".repeat(64) + ".js"]), /reserved/);
  assertSourcePaths(["assets/custom.json", "generated/custom.json"]);
  assert.deepEqual(transforms.map(item => item.id), ["dev-banner-v1", "shell-stamp-v2", "local-assets-v2", "channels-v1"]);
});

test("captured runtime and generator are byte-bound to their recorded source revision", () => {
  const provenance = JSON.parse(fs.readFileSync(path.join(fixture, "provenance.json")));
  assert.equal(provenance.sourceRevision, "9afd40ef4499da1b1cc9ade18e20ab596e4af6d2");
  for (const [file, expected] of Object.entries(provenance.files)) {
    assert.equal(hash(fs.readFileSync(path.join(fixture, "legacy", file))), expected, file);
  }
});

test("actual legacy fingerprint code preserves its original ordering, normalization and input exclusions", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "cg-legacy-fingerprint-"));
  try {
    const inputs = JSON.parse(fs.readFileSync(path.join(fixture, "fingerprint-inputs.json")));
    for (const [file, text] of Object.entries(inputs)) {
      const target = path.join(directory, file); fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, text);
    }
    const historical = require("./fixtures/docs-redesign/legacy/scripts/rebuild-docs.js");
    const actual = historical.canonicalInputFingerprint(directory).fingerprint;
    // Independent byte transcript of the small fixture, not a call to the new builder.
    const docs = Object.keys(inputs).filter(file => file.startsWith("docs/")).map(file =>
      `D:${file}\n${inputs[file].replace(/(<!-- cg:auto:commands -->\r?)[\s\S]*?(<!-- cg:auto:end -->)/, "$1<!--cg:auto-interior-->$2")}`).sort().join("\n");
    const parts = Object.keys(inputs).filter(file => file.startsWith(".github/prompts/") || file.startsWith("scripts/"))
      .map(file => `F:${file}\n${inputs[file]}`).concat(docs).sort().join("\n");
    assert.equal(actual, hash(parts));
    assert.equal(actual, "6fbce9bc8dac2322f5a2554b0734f0f9ba666723c86d7f81538c8bf0b7542d88");
    fs.writeFileSync(path.join(directory, "docs/index.md"), inputs["docs/index.md"].replace("generated A", "changed generated output"));
    fs.writeFileSync(path.join(directory, ".github/shared/ignored-v1.json"), "changed ignored registry");
    assert.equal(historical.canonicalInputFingerprint(directory).fingerprint, actual);
    fs.appendFileSync(path.join(directory, "docs/index.md"), "Changed manual bytes");
    assert.notEqual(historical.canonicalInputFingerprint(directory).fingerprint, actual);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
});

test("the frozen legacy producer emits the exact versionless metadata shape selected for recovery", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "cg-legacy-producer-"));
  try {
    fs.cpSync(path.join(__dirname, "fixtures/docs-automation/src/basic"), directory, { recursive: true });
    const historical = require("./fixtures/docs-redesign/legacy/scripts/rebuild-docs.js");
    assert.equal(historical.runRebuild(directory, { all: true }), 0);
    const metadata = JSON.parse(fs.readFileSync(path.join(directory, ".docs-build-metadata.json")));
    assert.equal(build().selectProducer(metadata, "compound-gpid-docs-producer-v1").fingerprintVersion, 1);
    assert.equal(historical.runRebuild(directory, { check: true, all: true }), 0);
    assert.equal(historical.verifyArtifact(directory), 0);
    assert.equal(metadata.site.fingerprint, historical.canonicalInputFingerprint(directory).fingerprint);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
});
