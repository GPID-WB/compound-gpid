"use strict";
// Fixed protocol limits, shared in Python by snapshot_contract.py. No filesystem I/O.
const crypto = require("node:crypto");
const { parseReleaseTag } = require("./release-version.js");
const MAX_ENVELOPE = 64 * 1024 * 1024, MAX_BYTES = 32 * 1024 * 1024;
const MAX_FILES = 10000, DEPLOYMENT_BYTES = 512 * 1024 * 1024;
const REQUIRED = ["index.html", "navigation.json", "assets/site.css", "assets/site.js", ".nojekyll"];
const hash = raw => crypto.createHash("sha256").update(raw).digest("hex");

// Fixed field order; ASCII path keys sort lexically, including integer keys.
// Construct JSON directly because JS object enumeration reorders integer keys.
function snapshotIdentity(record) {
  return "{" + ["schemaVersion", "kind", "tag", "sha", "runId", "runAttempt", "files"].map(key =>
    JSON.stringify(key) + ":" + (key === "files" ? "{" + Object.keys(record.files).sort().map(name =>
      JSON.stringify(name) + ":" + JSON.stringify(record.files[name])).join(",") + "}" : JSON.stringify(record[key]))).join(",") + "}";
}

function safeName(entry) {
  return !["__proto__", "constructor", "prototype", ".", ".."].includes(entry.toLowerCase())
    && /^[A-Za-z0-9_.+-]+$/.test(entry) && !/[.]$/.test(entry)
    && !/^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)/i.test(entry);
}

function validatePaths(paths, deployment = false) {
  if (!paths.length || paths.length > MAX_FILES) throw new Error("Snapshot file capacity limit");
  const nodes = new Map();
  for (const name of paths) {
    const parts = name.split("/");
    if (name.length > 255 || parts.length > 33 || parts.some(p => !safeName(p))) throw new Error("Unsafe snapshot path or depth limit");
    if (!deployment && ["dev", "releases"].includes(parts[0].toLowerCase())) throw new Error("Snapshot reserved path");
    for (let i = 0; i < parts.length; i++) {
      const node = parts.slice(0, i + 1).join("/"), key = node.toLowerCase();
      const identity = `${i === parts.length - 1 ? "file" : "dir"}:${node}`;
      if (nodes.has(key) && nodes.get(key) !== identity) throw new Error("Snapshot directory alias or file parent conflict");
      nodes.set(key, identity);
    }
  }
  if ([...nodes.values()].filter(v => v.startsWith("dir:")).length + 1 > MAX_FILES) throw new Error("Snapshot directory capacity limit");
}

function strictJson(raw) {
  // JSON.parse alone discards duplicate keys. Parse a bounded token stream first.
  const text = typeof raw === "string" ? raw : new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(raw);
  if (Buffer.byteLength(text) > MAX_ENVELOPE) throw new Error("Snapshot envelope limit");
  let at = 0;
  const space = () => { while (/[ \r\n\t]/.test(text[at] || "x")) at++; };
  function string() {
    const start = at++;
    while (at < text.length) {
      if (text[at] === "\\") at += 2;
      else if (text[at++] === '"') return JSON.parse(text.slice(start, at));
    }
    throw new Error("Invalid JSON string");
  }
  function value(depth) {
    space();
    if (depth > 40) throw new Error("Snapshot JSON depth limit");
    if (text[at] === '"') return string();
    if (text[at] === "{" || text[at] === "[") {
      const object = text[at++] === "{", end = object ? "}" : "]";
      const result = object ? {} : [];
      space();
      if (text[at] === end) { at++; return result; }
      while (at < text.length) {
        let key;
        if (object) {
          space();
          if (text[at] !== '"') throw new Error("Invalid JSON key");
          key = string(); space();
          if (Object.hasOwn(result, key) || text[at++] !== ":") throw new Error("Duplicate or invalid JSON key");
        }
        const next = value(depth + 1);
        if (object) Object.defineProperty(result, key, {value: next, enumerable: true}); else result.push(next);
        space();
        const delimiter = text[at++];
        if (delimiter === end) return result;
        if (delimiter !== ",") throw new Error("Invalid JSON delimiter");
      }
      throw new Error("Incomplete JSON");
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(text.slice(at));
    if (!token) throw new Error("Invalid JSON value");
    at += token[0].length;
    const result = JSON.parse(token[0]);
    if (typeof result === "number" && !Number.isFinite(result)) throw new Error("Nonfinite JSON number");
    return result;
  }
  const result = value(0); space();
  if (at !== text.length) throw new Error("Trailing JSON content");
  return result;
}

function validateRecord(record, expected = {}) {
  if (!record || Object.keys(record).sort().join() !== ["schemaVersion", "kind", "tag", "sha", "runId", "runAttempt", "files", "snapshotDigest"].sort().join()
      || record.schemaVersion !== 2 || !/^[0-9a-f]{40}$/.test(record.sha) || !["release", "dev"].includes(record.kind)
      || !Number.isSafeInteger(record.runId) || record.runId < 1 || !Number.isSafeInteger(record.runAttempt) || record.runAttempt < 1
      || !record.files || typeof record.files !== "object" || Array.isArray(record.files)) throw new Error("Invalid snapshot schema");
  if (record.kind === "release") parseReleaseTag(record.tag);
  else if (record.tag !== null) throw new Error("Dev snapshot claims release tag");
  validatePaths(Object.keys(record.files));
  if (record.kind === "dev") {
    const names = Object.keys(record.files), directories = new Set();
    for (const name of names) {
      const parts = name.split("/");
      for (let i = 1; i < parts.length; i++) directories.add(parts.slice(0, i).join("/"));
      if (name.length > 251 || parts.length > 32) throw new Error("Dev preview path capacity limit");
    }
    if (names.length > 1000 || directories.size > 1000) throw new Error("Dev preview capacity limit");
  }
  for (const name of REQUIRED) if (!Object.hasOwn(record.files, name)) throw new Error(`Snapshot is missing ${name}`);
  for (const digest of Object.values(record.files)) if (!/^[0-9a-f]{64}$/.test(digest)) throw new Error("Invalid snapshot digest");
  for (const [key, val] of Object.entries(expected)) if (record[key] !== val) throw new Error(`Snapshot ${key} identity mismatch`);
  const { snapshotDigest } = record;
  if (hash(snapshotIdentity(record)) !== snapshotDigest) throw new Error("Snapshot inventory identity differs");
}

function validateEnvelope(envelope, expected) {
  if (!envelope || Object.keys(envelope).sort().join() !== "files,record" || !envelope.files || Array.isArray(envelope.files)) throw new Error("Invalid snapshot envelope");
  validateRecord(envelope.record, expected);
  if (JSON.stringify(Object.keys(envelope.files).sort()) !== JSON.stringify(Object.keys(envelope.record.files).sort())) throw new Error("Snapshot envelope inventory differs");
  let total = 0;
  for (const [name, encoded] of Object.entries(envelope.files)) {
    if (typeof encoded !== "string") throw new Error("Invalid snapshot base64");
    const bytes = Buffer.from(encoded, "base64"); total += bytes.length;
    if (total > MAX_BYTES || bytes.toString("base64") !== encoded || hash(bytes) !== envelope.record.files[name]) throw new Error("Snapshot envelope capacity or digest differs");
  }
}

module.exports = { safeName, validatePaths, strictJson, validateRecord, validateEnvelope, snapshotIdentity,
  MAX_ENVELOPE, MAX_BYTES, MAX_FILES, DEPLOYMENT_BYTES };
