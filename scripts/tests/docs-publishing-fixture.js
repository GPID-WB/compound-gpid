"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const repository = path.resolve(__dirname, "../..");

/** Isolated source fixture with real canonical generator code and real upgraded shell. */
function modernSource() {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "cg-modern-source-"));
  for (const name of ["docs", ".github", "releases"]) fs.cpSync(path.join(repository, name), path.join(root, name), { recursive: true });
  fs.mkdirSync(path.join(root, "scripts"));
  for (const name of fs.readdirSync(path.join(repository, "scripts"))) {
    if (name.endsWith(".js")) fs.copyFileSync(path.join(repository, "scripts", name), path.join(root, "scripts", name));
  }
  fs.cpSync(path.join(repository, "scripts/docs-legacy-v1"), path.join(root, "scripts/docs-legacy-v1"), { recursive: true });
  return root;
}

/** Capture only isolated producer output, retaining source as pristine input. */
function modernArtifact(root) {
  const artifact = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "cg-modern-artifact-"));
  const { identifyProducer, expectedDocs } = require("../docs-provenance.js");
  const { digests, writeTree } = require("../docs-source.js");
  const producer = identifyProducer(root), docs = expectedDocs(root, producer);
  const metadata = { schemaVersion: 1, version: "1", producerContract: producer.producerContract,
    fingerprintVersion: producer.fingerprintVersion,
    site: { fingerprint: require("../docs-fingerprint.js").fingerprint(root, 2), files: digests(docs) } };
  const files = new Map([...docs].map(([n, v]) => [`docs/${n}`, v]));
  files.set(".docs-build-metadata.json", Buffer.from(JSON.stringify(metadata, null, 2) + "\n"));
  writeTree(artifact, files, [root]); return artifact;
}
module.exports = { modernSource, modernArtifact };
