"use strict";
// Complete immutable release-set loading. The caller supplies the existing payload
// validator and CLI error policy; this module never writes historical bytes.
const fs = require("node:fs"), path = require("node:path");
const { parseReleaseTag } = require("./release-version.js");

function loadReleasePayloads(root, validatePayload, fail) {
  const releasesDir = path.join(root, "releases");
  if (!fs.existsSync(releasesDir)) return [];
  if (fs.lstatSync(releasesDir).isSymbolicLink()) fail("releases directory must not be a symbolic link");
  const files = fs.readdirSync(releasesDir).filter(f => f.endsWith(".json") && f !== ".gitkeep").sort();
  const result = [];
  let latest = null;
  for (const file of files) {
    const full = path.join(releasesDir, file);
    if (fs.lstatSync(full).isSymbolicLink()) fail(`release file '${file}' must not be a symbolic link`);
    const raw = fs.readFileSync(full);
    let payload;
    try { payload = JSON.parse(new TextDecoder("utf-8", {fatal: true, ignoreBOM: true}).decode(raw)); }
    catch { fail(`release file '${file}' is not valid UTF-8 JSON`); }
    validatePayload(payload, file);
    if (file === "latest.json") { latest = {payload, raw}; continue; }
    try { parseReleaseTag(file.slice(0, -5)); }
    catch { fail(`release file '${file}' must use an immutable versioned filename`); }
    if (file !== `${payload.tag}.json`) fail(`release file '${file}' does not match payload tag '${payload.tag}'`);
    result.push({payload, file, raw});
  }
  if (result.length && !latest) fail("latest.json is required when immutable release payloads exist");
  if (latest) {
    const matching = result.find(r => r.payload.tag === latest.payload.tag && r.file === `${latest.payload.tag}.json`);
    if (!matching) fail(`latest.json tag '${latest.payload.tag}' has no immutable versioned payload`);
    if (!matching.raw.equals(latest.raw)) fail(`latest.json does not byte-match its versioned payload '${latest.payload.tag}'`);
  }
  const tags = new Set();
  for (const item of result) {
    if (tags.has(item.payload.tag)) fail(`duplicate immutable release tag '${item.payload.tag}'`);
    tags.add(item.payload.tag);
  }
  result.sort((a, b) => -a.payload.publishedAt.localeCompare(b.payload.publishedAt) || -a.payload.tag.localeCompare(b.payload.tag));
  if (latest && result.length && latest.payload.tag !== result[0].payload.tag) fail(`latest.json must match newest immutable payload '${result[0].payload.tag}'`);
  return result;
}

module.exports = { loadReleasePayloads };
