"use strict";
// Only controller-owned modules execute. Canonical producer trees are data.
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { execFileSync } = require("node:child_process");
const source = require("./docs-source.js");
const contract = require("./docs-build-contract.js");
const legacyFiles = ["rebuild-docs.js", "docs-markers.js", "generate-whats-new.js", "release-payloads.js", "release-version.js"];
const fail = message => { throw Error(`docs-provenance: ${message}`); };

/** Identify the canonical generator by protected code bytes, not artifact declarations. */
function identifyProducer(root) {
  source.unlinked(root);
  const script = path.join(root, "scripts/rebuild-docs.js");
  if (!fs.existsSync(script) || fs.lstatSync(script).isSymbolicLink()) fail("unknown canonical producer");
  const actual = source.hash(fs.readFileSync(script));
  let version;
  if (actual === contract.fingerprintContracts[1].generatorSha256) version = 1;
  else if (actual === source.hash(fs.readFileSync(path.join(__dirname, "rebuild-docs.js")))) version = 2;
  else fail("unknown canonical producer code");
  const protectedRoot = version === 1 ? path.join(__dirname, "docs-legacy-v1") : __dirname;
  const required = version === 1 ? legacyFiles : [...legacyFiles, "docs-provenance.js", "docs-source.js", "docs-build-contract.js", "docs-search-index.js", "docs-fingerprint.js"];
  for (const name of required) {
    const candidate = path.join(root, "scripts", name);
    if (fs.existsSync(candidate)) source.unlinked(candidate);
    if (!fs.existsSync(candidate) || fs.lstatSync(candidate).isSymbolicLink() ||
      !fs.readFileSync(candidate).equals(fs.readFileSync(path.join(protectedRoot, name)))) fail(`canonical producer code mismatch: ${name}`);
  }
  if (version === 2) {
    for (const name of contract.ASSET_SOURCES.filter(n => n.endsWith(".js"))) {
      const candidate = path.join(root, "docs", name);
      if (!fs.existsSync(candidate) || fs.lstatSync(candidate).isSymbolicLink() ||
        !fs.readFileSync(candidate).equals(fs.readFileSync(path.join(__dirname, "../docs", name)))) fail(`unknown canonical runtime/helper: ${name}`);
    }
  }
  return contract.producers[`compound-gpid-docs-producer-v${version}`];
}

/** Independently regenerate managed bytes in isolated data-only staging. */
function expectedDocs(root, producer = identifyProducer(root)) {
  const stage = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "cg-expected-docs-"));
  try {
    for (const dir of ["docs", ".github/prompts", ".github/shared", "releases"]) {
      const input = path.join(root, dir);
      if (!fs.existsSync(input)) continue;
      for (const [name, bytes] of source.readTree(input)) {
        const target = path.join(stage, dir, name); fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, bytes);
      }
    }
    const builder = path.join(__dirname, producer.fingerprintVersion === 1 ? "docs-legacy-v1/rebuild-docs.js" : "rebuild-docs.js");
    try { execFileSync(process.execPath, [builder, "--root", stage, "--all"], { encoding: "utf8", timeout: 30000, maxBuffer: 1048576 }); }
    catch (error) { fail(`expected generation failed: ${String(error.stderr || error.message).slice(0, 1000)}`); }
    return source.readTree(path.join(stage, "docs"));
  } finally { fs.rmSync(stage, { recursive: true, force: true }); }
}

/** Verify derivation before importing; rejects self-consistent forged generated/unmanaged files. */
function verifyProducer(root, artifact) {
  const inventory = source.readTree(artifact);
  if (!inventory.has(".docs-build-metadata.json") || [...inventory.keys()].some(n => n !== ".docs-build-metadata.json" && !n.startsWith("docs/"))) fail("unexpected artifact root inventory");
  const metadata = JSON.parse(inventory.get(".docs-build-metadata.json"));
  if (metadata.producerContract !== undefined && (metadata.schemaVersion !== 1 || metadata.version !== "1" ||
    Object.keys(metadata).sort().join() !== "fingerprintVersion,producerContract,schemaVersion,site,version" ||
    Object.keys(metadata.site || {}).sort().join() !== "files,fingerprint")) fail("invalid versioned producer metadata shape");
  const actual = new Map([...inventory].filter(([n]) => n.startsWith("docs/")).map(([n, v]) => [n.slice(5), v]));
  if (JSON.stringify(Object.keys(metadata.site?.files || {}).sort()) !== JSON.stringify([...actual.keys()].sort())) fail("artifact file list mismatch");
  const hashes = source.digests(actual);
  for (const [name, hash] of Object.entries(hashes)) if (metadata.site.files[name] !== hash) fail("artifact digest mismatch");
  const producer = identifyProducer(root);
  contract.selectProducer(metadata, producer.producerContract);
  const fingerprint = require("./docs-fingerprint.js").fingerprint(root, producer.fingerprintVersion);
  if (fingerprint !== metadata.site.fingerprint) fail("canonical source fingerprint mismatch");
  const expected = expectedDocs(root, producer);
  source.equalFiles(actual, expected, "producer derivation");
  return { producer, fingerprint, files: expected, metadata };
}

/** The third argument is mandatory: canonical roots are never import destinations. */
function importVerified(root, artifact, staging) {
  if (!staging) fail("separate staging directory is required");
  source.separate(staging, [root, artifact]);
  const verified = verifyProducer(root, artifact);
  const files = new Map([...verified.files].map(([n, v]) => [`docs/${n}`, v]));
  files.set(".docs-build-metadata.json", Buffer.from(JSON.stringify(verified.metadata, null, 2) + "\n"));
  source.writeTree(staging, files, [root, artifact]);
  return staging;
}
module.exports = { identifyProducer, expectedDocs, verifyProducer, importVerified };
