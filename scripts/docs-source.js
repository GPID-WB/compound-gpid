"use strict";
// Bounded data reads shared by protected documentation verification and builds.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const fail = message => { throw Error(`docs-source: ${message}`); };

/** Reject links anywhere in an existing input path, including its ancestors. */
function unlinked(input) {
  const absolute = path.resolve(input);
  if (fs.realpathSync(absolute) !== absolute) fail("symbolic or linked source path forbidden");
  return absolute;
}

/** Read regular files only; symlinks/hardlinks cannot import code or escape roots. */
function readTree(root) {
  unlinked(root);
  const files = new Map(); let bytes = 0;
  function walk(dir, prefix = "", depth = 0) {
    const info = fs.lstatSync(dir);
    if (!info.isDirectory() || info.isSymbolicLink() || depth > 32) fail("linked or invalid source directory");
    for (const name of fs.readdirSync(dir).sort()) {
      if (!name || /[\\\x00-\x1f]/.test(name)) fail("unsafe source filename");
      const file = path.join(dir, name), relative = prefix + name, stat = fs.lstatSync(file);
      if (stat.isSymbolicLink()) fail(`symbolic link forbidden: ${relative}`);
      if (stat.isDirectory()) walk(file, `${relative}/`, depth + 1);
      else {
        if (!stat.isFile() || stat.nlink !== 1 || stat.size > 67108864 ||
          (bytes += stat.size) > 268435456 || files.size >= 10000) fail("invalid source inventory capacity");
        files.set(relative, fs.readFileSync(file));
      }
    }
  }
  walk(root); return files;
}

/** Return deterministic hashes for independently read bytes. Example: digests(readTree(root)). */
function digests(files) { return Object.fromEntries([...files].map(([name, bytes]) => [name, hash(bytes)]).sort()); }

/** Compare full inventory and exact bytes, never merely a producer's self-digests. */
function equalFiles(actual, expected, label) {
  if (actual.size !== expected.size) fail(`${label} file list differs from canonical expected output`);
  for (const [name, bytes] of expected) {
    if (!actual.get(name)?.equals(bytes)) fail(`${label} differs from canonical expected output: ${name}`);
  }
}

/** Reject output/source overlap before any write, including symlinked parent paths. */
function separate(output, inputs) {
  const absolute = path.resolve(output);
  let probe = absolute;
  while (!fs.existsSync(probe)) probe = path.dirname(probe);
  if (path.resolve(fs.realpathSync(probe)) !== probe) fail("output parent must not follow a symbolic link");
  for (const input of inputs.map(value => path.resolve(value))) {
    for (const [left, right] of [[input, absolute], [absolute, input]]) {
      const relative = path.relative(left, right);
      if (!relative || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative))) fail("output overlaps canonical source or artifact");
    }
  }
  return absolute;
}

/** Promote only after callers finish validation; invalid input leaves prior output untouched. */
function writeTree(output, files, inputs = []) {
  const target = separate(output, inputs), parent = path.dirname(target);
  fs.mkdirSync(parent, { recursive: true });
  const staging = fs.mkdtempSync(path.join(parent, ".docs-verified-"));
  try {
    for (const [name, bytes] of files) {
      if (name.startsWith("/") || name.split("/").some(p => !p || p === "." || p === "..") || name.includes("\\")) fail("unsafe output path");
      const file = path.join(staging, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes);
    }
    if (fs.existsSync(target)) {
      if (!fs.lstatSync(target).isDirectory() || fs.lstatSync(target).isSymbolicLink()) fail("invalid output directory");
      fs.rmSync(target, { recursive: true });
    }
    fs.renameSync(staging, target);
  } finally { if (fs.existsSync(staging)) fs.rmSync(staging, { recursive: true, force: true }); }
}
module.exports = { readTree, hash, digests, equalFiles, separate, writeTree, unlinked };
