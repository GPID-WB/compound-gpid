"use strict";
// scripts/generate-whats-new.js
// Deterministic, dependency-free What's New generator for Compound GPID.
//
// Reads `releases/*.json` release payloads (excluding `.gitkeep`), deduplicates
// `latest.json` against its immutable versioned record, validates every payload,
// and renders a stable newest-first release history inside the `release-notes`
// marker pair of `docs/whats-new.md`.
//
// Modes:
//   default                  write mode (replace marker interior, write only on change)
//   --check                  no-write; exit 1 naming the stale file, exit 0 when current
//   --validate-payload <rel> machine-checkable payload validation; exit 0/1
//   --validate-release-set   validate all immutable payload/latest invariants
//
// Path safety and payload validation mirror the release-payload contract:
// strict schema, bounded plain text, allowed kinds, durable tag/URL shapes.

const fs = require("node:fs");
const path = require("node:path");
const { findManagedMarkers, replaceManagedInterior } = require("./docs-markers.js");

const ALLOWED_KINDS = new Set(["new", "fixed", "internal"]);
const MAX_RELEASES = 20;
const MAX_TITLE_LEN = 120;
const MAX_ENTRY_LEN = 500;
const MAX_ENTRIES = 50;
const REPOSITORY = "GPID-WB/compound-gpid";

const OPEN = "<!-- cg:auto:release-notes -->";
const CLOSE = "<!-- cg:auto:end -->";
const EMPTY_STATE = "No releases published yet.\n";

function usage() {
  console.error(
    "Usage: node scripts/generate-whats-new.js [--root <path>] [--check] [--validate-payload <rel>] [--validate-release-set]"
  );
  process.exit(2);
}

function parseArgs(argv) {
  const args = { root: process.cwd(), check: false, validatePayload: null, validateReleaseSet: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") args.root = path.resolve(argv[++i]);
    else if (a === "--check") args.check = true;
    else if (a === "--validate-payload") args.validatePayload = argv[++i];
    else if (a === "--validate-release-set") args.validateReleaseSet = true;
    else return null;
  }
  return args;
}

function fail(message) {
  console.error(`generate-whats-new: ${message}`);
  process.exit(1);
}

function resolveInside(root, rel) {
  const target = path.resolve(root, rel);
  const rootResolved = fs.realpathSync(root);
  const relPath = path.relative(rootResolved, fs.realpathSync(target));
  if (relPath.startsWith("..") || path.isAbsolute(relPath)) fail(`path escapes repository root: ${rel}`);
  return path.resolve(rootResolved, relPath);
}

// ---------------------------------------------------------------------------
// Payload validation
// ---------------------------------------------------------------------------

function isIsoUtc(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)) return false;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return false;
  const canonical = d.toISOString().replace(/\.000Z$/, "Z");
  return canonical === value;
}

function isIsoDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const d = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value;
}

function isGitHubReleaseUrl(value, tag) {
  return (
    typeof value === "string" &&
    new RegExp(`^https://github\\.com/${REPOSITORY}/releases/tag/${escapeRegExp(tag)}$`).test(value)
  );
}

function isGitHubTagUrl(value, tag) {
  return (
    typeof value === "string" &&
    new RegExp(`^https://github\\.com/${REPOSITORY}/tree/${escapeRegExp(tag)}$`).test(value)
  );
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasControlChars(value) {
  return /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(value);
}

function validatePayload(payload, sourceName) {
  const label = `payload ${sourceName}`;
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) fail(`${label} is not an object`);
  if (payload.schemaVersion !== 1) fail(`${label} has invalid schemaVersion`);
  if (typeof payload.tag !== "string" || !/^v\d+\.\d+\.\d+(\.\d+)?$/.test(payload.tag)) {
    fail(`${label} has invalid tag '${payload.tag}'`);
  }
  if (!isIsoUtc(payload.publishedAt)) fail(`${label} has malformed publishedAt '${payload.publishedAt}'`);
  if (typeof payload.name !== "string" || !payload.name.length || payload.name.length > 200 || hasControlChars(payload.name)) {
    fail(`${label} has invalid name`);
  }
  if (!isGitHubReleaseUrl(payload.url, payload.tag)) fail(`${label} has invalid GitHub release URL`);
  if (!isGitHubTagUrl(payload.sourceUrl, payload.tag)) fail(`${label} has invalid sourceUrl for tag '${payload.tag}'`);
  if (payload.releaseDate !== undefined && !isIsoDate(payload.releaseDate)) {
    fail(`${label} has invalid releaseDate`);
  }
  if (!Array.isArray(payload.sections) || payload.sections.length === 0) {
    fail(`${label} must have a non-empty sections array`);
  }
  const seenSectionKeys = new Set();
  for (const section of payload.sections) {
    if (!section || typeof section !== "object") fail(`${label} has a non-object section`);
    if (!ALLOWED_KINDS.has(section.kind)) fail(`${label} has unknown kind '${section.kind}'`);
    if (typeof section.title !== "string" || !section.title.length || section.title.length > MAX_TITLE_LEN) {
      fail(`${label} has invalid section title`);
    }
    if (hasControlChars(section.title)) fail(`${label} section title has control characters`);
    if (!Array.isArray(section.entries) || section.entries.length === 0 || section.entries.length > MAX_ENTRIES) {
      fail(`${label} section entries are missing or excessive`);
    }
    for (const entry of section.entries) {
      if (typeof entry !== "string" || !entry.length || entry.length > MAX_ENTRY_LEN) {
        fail(`${label} has an invalid entry`);
      }
      if (hasControlChars(entry)) fail(`${label} entry has control characters`);
    }
    // A section is identified by kind (one controlled section per kind is the
    // deterministic contract for rendering groups).
    if (seenSectionKeys.has(section.kind)) fail(`${label} has duplicate kind '${section.kind}'`);
    seenSectionKeys.add(section.kind);
  }
  const unknownTop = Object.keys(payload).filter(
    (k) => !["schemaVersion", "tag", "publishedAt", "name", "url", "sourceUrl", "sections", "releaseDate"].includes(k)
  );
  if (unknownTop.length) fail(`${label} has unrecognized field '${unknownTop[0]}'`);
}

// ---------------------------------------------------------------------------
// Loading release files
// ---------------------------------------------------------------------------

function loadReleasePayloads(root) {
  const releasesDir = path.join(root, "releases");
  if (!fs.existsSync(releasesDir)) return [];
  if (fs.lstatSync(releasesDir).isSymbolicLink()) fail("releases directory must not be a symbolic link");
  const files = fs.readdirSync(releasesDir)
    .filter((f) => f.endsWith(".json") && f !== ".gitkeep")
    .sort();
  const versioned = [];
  let latest = null;
  for (const file of files) {
    const full = path.join(releasesDir, file);
    if (fs.lstatSync(full).isSymbolicLink()) fail(`release file '${file}' must not be a symbolic link`);
    const raw = fs.readFileSync(full, "utf8");
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      fail(`release file '${file}' is not valid JSON`);
    }
    validatePayload(payload, file);
    if (file === "latest.json") {
      latest = { payload, raw };
      continue;
    }
    if (!/^v\d+\.\d+\.\d+(\.\d+)?\.json$/.test(file)) {
      fail(`release file '${file}' must use an immutable versioned filename`);
    }
    if (file !== `${payload.tag}.json`) fail(`release file '${file}' does not match payload tag '${payload.tag}'`);
    versioned.push({ payload, file, raw });
  }
  const result = versioned.map((v) => ({ payload: v.payload, file: v.file, raw: v.raw }));
  if (result.length && !latest) fail("latest.json is required when immutable release payloads exist");
  // latest.json must be a byte-for-byte current-release convenience copy of an
  // immutable versioned payload; never render it as a second release.
  if (latest) {
    const match = result.find(
      (r) => r.payload.tag === latest.payload.tag && r.file === `${latest.payload.tag}.json`
    );
    const versionedTag = result.find((r) => r.payload.tag === latest.payload.tag);
    if (!match || !versionedTag) fail(`latest.json tag '${latest.payload.tag}' has no immutable versioned payload`);
    if (versionedTag.raw !== latest.raw) fail(`latest.json does not byte-match its versioned payload '${latest.payload.tag}'`);
  }
  // Reject duplicate tags across immutable payloads.
  const tags = new Set();
  for (const r of result) {
    if (tags.has(r.payload.tag)) fail(`duplicate immutable release tag '${r.payload.tag}'`);
    tags.add(r.payload.tag);
  }
  // Stable newest-first ordering by publishedAt then tag.
  result.sort((a, b) => {
    const da = a.payload.publishedAt.localeCompare(b.payload.publishedAt);
    if (da !== 0) return -da;
    return -a.payload.tag.localeCompare(b.payload.tag);
  });
  if (latest && result.length && latest.payload.tag !== result[0].payload.tag) {
    fail(`latest.json must match newest immutable payload '${result[0].payload.tag}'`);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Rendering (plain Markdown, escaped, inert)
// ---------------------------------------------------------------------------

function escapeText(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\|/g, "\\|")
    .replace(/\[/g, "&#91;")
    .replace(/\]/g, "&#93;")
    .replace(/\r?\n/g, "<br>");
}

function renderEntry(entry) {
  return `- ${escapeText(entry)}`;
}

function renderSection(section) {
  const label = { new: "New", fixed: "Fixed", internal: "Internal" }[section.kind];
  const lines = [`**${label} — ${escapeText(section.title)}**`];
  for (const entry of section.entries) {
    lines.push(renderEntry(entry));
  }
  return lines.join("\n");
}

function renderReleases(payloads) {
  const blocks = payloads.map((r) => {
    const p = r.payload;
    const header = `### ${escapeText(p.tag)} — ${escapeText(p.name)}\n\n*${escapeText(p.publishedAt)}*`;
    const sections = p.sections.map((s) => renderSection(s)).join("\n\n");
    const link = `[View source tag](${escapeText(p.sourceUrl)})`;
    return `${header}\n\n${sections}\n\n${link}`;
  });
  const historyLink = payloads.length > MAX_RELEASES
    ? `\n\n[View older releases](${githubReleasesUrl(payloads[0].payload.sourceUrl)})`
    : "";
  return blocks.slice(0, MAX_RELEASES).join("\n\n---\n\n") + historyLink + "\n";
}

function githubReleasesUrl(sourceUrl) {
  const m = /^(https:\/\/github\.com\/GPID-WB\/compound-gpid)\/tree\//.exec(sourceUrl);
  if (!m) fail(`cannot derive GitHub Releases URL from sourceUrl '${sourceUrl}'`);
  return `${m[1]}/releases`;
}

// ---------------------------------------------------------------------------
// Generator entry points
// ---------------------------------------------------------------------------

function whatsNewPath(root) {
  return path.join(root, "docs", "whats-new.md");
}

function verifyMarkerPair(text) {
  let markers;
  try {
    markers = findManagedMarkers(text);
  } catch (err) {
    fail(err.message);
  }
  if (markers.length !== 1 || markers[0].section !== "release-notes") {
    fail("docs/whats-new.md is missing the release-notes marker pair");
  }
  return markers[0];
}

function expectedPage(text, payloads) {
  verifyMarkerPair(text);
  const interior = payloads.length ? renderReleases(payloads) : EMPTY_STATE;
  try {
    return replaceManagedInterior(text, "release-notes", interior);
  } catch (err) {
    fail(err.message);
  }
}

function prepareReleaseNotes(root) {
  resolveInside(root, "docs/whats-new.md");
  const filePath = whatsNewPath(root);
  if (!fs.existsSync(filePath)) fail(`docs/whats-new.md missing: ${filePath}`);
  const text = fs.readFileSync(filePath, "utf8");
  const payloads = loadReleasePayloads(root);
  const next = expectedPage(text, payloads);
  return { filePath, text, next, payloads, changed: next !== text };
}

function runReleaseNotes(root, { check = false } = {}) {
  const build = prepareReleaseNotes(root);
  if (check) {
    if (!build.changed) {
      console.log("generate-whats-new: current");
      return 0;
    }
    console.log("docs/whats-new.md");
    return 1;
  }
  if (build.changed) fs.writeFileSync(build.filePath, build.next);
  console.log(build.payloads.length ? `generate-whats-new: wrote ${Math.min(build.payloads.length, MAX_RELEASES)} release(s)` : "generate-whats-new: wrote empty state");
  return 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) usage();
  try {
    if (args.validatePayload) {
      const rel = args.validatePayload;
      const full = resolveInside(args.root, rel);
      if (!fs.existsSync(full)) fail(`payload file missing: ${rel}`);
      const payload = JSON.parse(fs.readFileSync(full, "utf8"));
      validatePayload(payload, rel);
      console.log(`generate-whats-new: payload valid (${rel})`);
      process.exitCode = 0;
      return;
    }
    if (args.validateReleaseSet) {
      const payloads = loadReleasePayloads(args.root);
      console.log(`generate-whats-new: release set valid (${payloads.length} immutable payload(s))`);
      process.exitCode = 0;
      return;
    }
    process.exitCode = runReleaseNotes(args.root, { check: args.check });
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    if (!/^generate-whats-new:/.test(msg)) console.error(`generate-whats-new: ${msg}`);
    else console.error(msg);
    process.exitCode = 1;
  }
}

if (require.main === module) main();

module.exports = { runReleaseNotes, prepareReleaseNotes, loadReleasePayloads, validatePayload, renderReleases, escapeText };
