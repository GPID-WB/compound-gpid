"use strict";
const fs = require("node:fs");
const path = require("node:path");
const { readTree, hash, unlinked } = require("./docs-source.js");
const { fingerprintContracts, assertSourcePaths } = require("./docs-build-contract.js");
const { normalizeManagedInteriors } = require("./docs-markers.js");

/** Versioned canonical-input hash. V1 delegates to the exact protected legacy algorithm. */
function fingerprint(root, version) {
  unlinked(root);
  if (version === 1) return require("./docs-legacy-v1/rebuild-docs.js").canonicalInputFingerprint(root).fingerprint;
  if (version !== 2) throw Error("Unknown documentation fingerprint version");
  const rules = fingerprintContracts[2], inputs = new Map();
  function add(name, bytes) {
    if (rules.generatedOutputs.includes(name)) return;
    let text = bytes.toString("utf8").replace(/\r\n?/g, "\n");
    if (name.startsWith("docs/")) text = normalizeManagedInteriors(text);
    inputs.set(name, text);
  }
  for (const [dir, extensions] of Object.entries(rules.directoryInputs)) {
    if (!fs.existsSync(path.join(root, dir))) { inputs.set(dir, null); continue; }
    const files = readTree(path.join(root, dir));
    if (!files.size) inputs.set(dir, []);
    for (const [name, bytes] of files) if (extensions.some(ext => name.endsWith(ext))) add(`${dir}/${name}`, bytes);
  }
  for (const dir of rules.treeInputs) {
    if (!fs.existsSync(path.join(root, dir))) { inputs.set(dir, null); continue; }
    const files = readTree(path.join(root, dir));
    if (dir === "docs") assertSourcePaths([...files.keys()]);
    if (!files.size) inputs.set(dir, []);
    for (const [name, bytes] of files) add(`${dir}/${name}`, bytes);
  }
  for (const name of rules.fixedInputs) {
    const file = path.join(root, name);
    if (!fs.existsSync(file)) { inputs.set(name, null); continue; }
    unlinked(file);
    if (!fs.lstatSync(file).isFile() || fs.lstatSync(file).nlink !== 1) throw Error("Linked or invalid fingerprint input");
    add(name, fs.readFileSync(file));
  }
  return hash(JSON.stringify([...inputs].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)));
}
module.exports = { fingerprint };
