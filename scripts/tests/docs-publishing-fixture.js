"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const repository = path.resolve(__dirname, "../..");

/** Isolated source fixture with real canonical generator code and real upgraded shell. */
function modernSource() {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), "cg-modern-source-"));
  for (const name of ["docs", ".github", "releases", "scripts", "bin", "install.ps1", ".gitattributes"]) {
    fs.cpSync(path.join(repository, name), path.join(root, name), { recursive: true,
      filter: file => !file.includes("__pycache__") && !file.endsWith(".pyc") });
  }
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
    site: { fingerprint: require("../docs-fingerprint.js").fingerprint(root, producer.fingerprintVersion), files: digests(docs) } };
  const files = new Map([...docs].map(([n, v]) => [`docs/${n}`, v]));
  files.set(".docs-build-metadata.json", Buffer.from(JSON.stringify(metadata, null, 2) + "\n"));
  writeTree(artifact, files, [root]); return artifact;
}
module.exports = { modernSource, modernArtifact };
