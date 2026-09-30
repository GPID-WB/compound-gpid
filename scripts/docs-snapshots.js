"use strict";

// Static-data snapshot operations. Run identity must also be checked through the
// trusted provider; an internally consistent manifest is not publication authority.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { parseReleaseTag, compareReleaseTags } = require("./release-version.js");
const { safeName, validatePaths, strictJson, validateRecord, validateEnvelope, snapshotIdentity,
  MAX_ENVELOPE, MAX_BYTES, MAX_FILES, DEPLOYMENT_BYTES } = require("./snapshot-data.js");
const REQUIRED = ["index.html", "navigation.json", "assets/site.css", "assets/site.js", ".nojekyll"];
const SHA = /^[0-9a-f]{40}$/;
const META = ".docs-snapshot.json";
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const canonical = value => JSON.stringify(value, Object.keys(value).sort());

function ensureParent(output) {
  const parent = path.dirname(path.resolve(output));
  if (!fs.existsSync(parent)) { ensureParent(parent); fs.mkdirSync(parent); }
  directory(parent);
}

function directory(root) {
  const absolute = path.resolve(root);
  const stat = fs.lstatSync(absolute), real = fs.realpathSync(absolute);
  const equal = process.platform === "win32" ? real.toLowerCase() === absolute.toLowerCase() : real === absolute;
  if (stat.isSymbolicLink() || !equal || !stat.isDirectory())
    throw new Error("Snapshot directory must not follow a link");
  return absolute;
}

function inventory(root, maxBytes = DEPLOYMENT_BYTES) {
  directory(root);
  const files = Object.create(null), seen = new Set();
  let bytes = 0, directories = 0, count = 0;
  function walk(current, prefix, depth = 0) {
    if (++directories > 10000 || depth > 32) throw new Error("Snapshot directory limits exceeded");
    for (const entry of fs.readdirSync(current).sort()) {
      if (!safeName(entry))
        throw new Error("Unsafe snapshot path");
      const relative = prefix + entry, full = path.join(current, entry);
      if (relative.length > 255) throw new Error("Snapshot path length limit");
      if (seen.has(relative.toLowerCase())) throw new Error("Case-fold snapshot collision");
      seen.add(relative.toLowerCase());
      const stat = fs.lstatSync(full);
      if (stat.isSymbolicLink()) throw new Error("Snapshot contains a link");
      if (stat.isDirectory()) { directory(full); walk(full, relative + "/", depth + 1); }
      else if (stat.isFile() && stat.nlink === 1) {
        bytes += stat.size;
        if (stat.size > MAX_BYTES || bytes > maxBytes || ++count > MAX_FILES)
          throw new Error("Snapshot inventory exceeds limits");
        files[relative] = hash(fs.readFileSync(full));
      } else throw new Error("Snapshot contains a nonregular or hardlinked file");
    }
  }
  walk(root, "");
  return files;
}

function identity(metadata) {
  return hash(snapshotIdentity(metadata));
}

function writeArtifact(out, copies, metadata, filename) {
  validatePaths(Object.keys(metadata.files), filename === ".docs-deployment.json");
  let bytes = 0;
  for (const { root, files } of copies) for (const relative of Object.keys(files)) {
    bytes += fs.lstatSync(path.join(root, relative)).size;
  }
  if (bytes > (filename === META ? MAX_BYTES : DEPLOYMENT_BYTES)) throw new Error("Snapshot aggregate capacity limit");
  // Exclusive directory creation preserves concurrent output instead of clobbering it.
  ensureParent(out);
  fs.mkdirSync(out);
  fs.mkdirSync(path.join(out, "site"));
  for (const { root, prefix, files } of copies) {
    for (const relative of Object.keys(files)) {
      const destination = path.join(out, "site", prefix, relative);
      fs.mkdirSync(path.dirname(destination), { recursive: true });
      fs.copyFileSync(path.join(root, relative), destination, fs.constants.COPYFILE_EXCL);
    }
  }
  const actual = inventory(path.join(out, "site"));
  if (canonical(actual) !== canonical(metadata.files)) throw new Error("Snapshot changed while copying inventory");
  fs.writeFileSync(path.join(out, filename), JSON.stringify(metadata, null, 2) + "\n", { flag: "wx" });
  return JSON.parse(JSON.stringify(metadata));
}

function buildSnapshot({ root, out, kind, tag, sha, runId, runAttempt }) {
  if (!["release", "dev"].includes(kind) || !SHA.test(sha) || !Number.isSafeInteger(runId) || runId < 1 || !Number.isSafeInteger(runAttempt) || runAttempt < 1)
    throw new Error("Invalid snapshot source/run identity");
  if (kind === "release") parseReleaseTag(tag);
  else if (tag !== null) throw new Error("Dev snapshot must not claim a release tag");
  const docs = path.join(directory(root), "docs"), files = inventory(docs, MAX_BYTES);
  for (const name of REQUIRED) if (!files[name]) throw new Error(`Snapshot is missing ${name}`);
  validatePaths(Object.keys(files));
  const record = { schemaVersion: 2, kind, tag, sha, runId, runAttempt, files };
  if (kind === "dev" && Object.keys(files).length > 1000) throw new Error("Dev preview capacity limit");
  record.snapshotDigest = identity(record);
  validateRecord(record);
  return writeArtifact(out, [{ root: docs, prefix: "", files }], record, META);
}

function verifySnapshot(artifact, expected = {}) {
  directory(artifact);
  const meta = path.join(artifact, META), stat = fs.lstatSync(meta);
  if (!stat.isFile() || stat.nlink !== 1 || stat.size > 4 * 1024 * 1024) throw new Error("Invalid snapshot metadata file");
  const value = strictJson(fs.readFileSync(meta));
  validateRecord(value, expected);
  const actual = inventory(path.join(artifact, "site"), MAX_BYTES);
  if (canonical(actual) !== canonical(Object.fromEntries(Object.entries(value.files).sort()))) throw new Error("Snapshot inventory mismatch");
  return value;
}

function composeSnapshots({ releases, dev, out, composerRevision, currentDevSha, stableTag }) {
  if (!SHA.test(composerRevision) || !SHA.test(currentDevSha) || !Array.isArray(releases) || !releases.length)
    throw new Error("Invalid composition identity");
  const snapshots = releases.map(artifact => ({ artifact, record: verifySnapshot(artifact, { kind: "release" }) }));
  const stable = snapshots.filter(({ record }) => {
    const parsed = parseReleaseTag(record.tag);
    return !parsed.legacy && !parsed.prerelease.length;
  }).sort((a, b) => -compareReleaseTags(a.record.tag, b.record.tag));
  if (!stable.length || stable[0].record.tag !== stableTag) throw new Error("Selected stable release must be the highest stable policy selection");
  const preview = verifySnapshot(dev, { kind: "dev" });
  if (preview.sha !== currentDevSha) throw new Error("Dev snapshot is stale; refresh only the mutable preview");
  const copies = [], files = Object.create(null);
  function include(artifact, record, prefix) {
    for (const [name, digest] of Object.entries(record.files)) {
      const destination = prefix + name;
      if (Object.hasOwn(files, destination)) throw new Error("Duplicate snapshot destination");
      files[destination] = digest;
    }
    copies.push({ root: path.join(artifact, "site"), files: record.files, prefix });
  }
  include(stable[0].artifact, stable[0].record, "");
  for (const { artifact, record } of snapshots) include(artifact, record, `releases/${record.tag}/`);
  include(dev, preview, "dev/");
  const record = { schemaVersion: 2, composerRevision, stableTag,
    releases: snapshots.map(({ record: item }) => ({ tag: item.tag, sha: item.sha, runId: item.runId, runAttempt: item.runAttempt, snapshotDigest: item.snapshotDigest })),
    dev: { sha: preview.sha, runId: preview.runId, runAttempt: preview.runAttempt, snapshotDigest: preview.snapshotDigest }, files };
  return writeArtifact(out, copies, record, ".docs-deployment.json");
}

function verifyComposition(artifact, expected) {
  directory(artifact);
  const file = path.join(artifact, ".docs-deployment.json"), stat = fs.lstatSync(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1 || stat.size > 8 * 1024 * 1024) throw new Error("Invalid composition metadata");
  const record = JSON.parse(fs.readFileSync(file, "utf8"));
  if (JSON.stringify(record) !== JSON.stringify(expected) || record.schemaVersion !== 2
      || canonical(inventory(path.join(artifact, "site"))) !== canonical(record.files)) throw new Error("Composition inventory mismatch");
  return record;
}

function exportSnapshot(artifact, destination) {
  const record = verifySnapshot(artifact), files = Object.create(null);
  for (const name of Object.keys(record.files)) files[name] = fs.readFileSync(path.join(artifact, "site", name)).toString("base64");
  const raw = JSON.stringify({record, files}) + "\n";
  if (Buffer.byteLength(raw) > MAX_ENVELOPE) throw new Error("Snapshot envelope capacity limit");
  fs.writeFileSync(destination, raw, {flag: "wx"});
}

function importSnapshot(source, out, expected) {
  const stat = fs.lstatSync(source);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1 || stat.size > MAX_ENVELOPE) throw new Error("Invalid snapshot envelope");
  const envelope = strictJson(fs.readFileSync(source));
  validateEnvelope(envelope, expected);
  ensureParent(out);
  fs.mkdirSync(out);
  directory(out);
  fs.mkdirSync(path.join(out, "site"));
  for (const [name, encoded] of Object.entries(envelope.files)) {
    const bytes = Buffer.from(encoded, "base64");
    if (bytes.toString("base64") !== encoded || hash(bytes) !== envelope.record.files[name]) throw new Error("Snapshot envelope digest differs");
    const target = path.join(out, "site", name);
    fs.mkdirSync(path.dirname(target), {recursive: true});
    fs.writeFileSync(target, bytes, {flag: "wx"});
  }
  fs.writeFileSync(path.join(out, META), JSON.stringify(envelope.record), {flag: "wx"});
  return verifySnapshot(out, expected);
}

module.exports = { buildSnapshot, verifySnapshot, composeSnapshots, inventory, verifyComposition, exportSnapshot, importSnapshot };

if (require.main === module) {
  const [operation, input, output] = process.argv.slice(2);
  if (operation === "build") buildSnapshot(JSON.parse(fs.readFileSync(input, "utf8")));
  else if (operation === "export") exportSnapshot(input, output);
  else if (operation === "import") importSnapshot(input, output);
  else if (operation === "compose") composeSnapshots(JSON.parse(fs.readFileSync(input, "utf8")));
  else if (operation === "verify") verifySnapshot(input);
  else throw new Error("Unknown snapshot operation");
}
