"use strict";
// scripts/rebuild-docs.js
// Deterministic, dependency-free documentation rebuild for Compound GPID.
//
// Ownership contract (docs/_wiki.yml):
//   - `commands`          -> regenerated from .github/prompts/cg-*.prompt.md
//   - `research-commands` -> regenerated from .github/prompts/cr-*.prompt.md
//   - `release-notes`     -> owned by the release generator (generate-whats-new.js)
//   - Any other declared managed section has no owner -> explicit failure.
//
// Modes:
//   default                   write mode (replace marker interiors, write only on change)
//   --check                   no-write; exit 1 naming stale files, exit 0 when current
//   --all                     complete deployable site build (includes What's New) +
//                             out-of-tree build metadata (version, canonical-input
//                             fingerprint, per-file digests)
//   --verify-fingerprint <path>  no-write; recompute the normalized canonical-input
//                             fingerprint and compare with downloaded build metadata
//   --verify-artifact <dir>      no-write; verify every downloaded docs file against
//                             the build metadata stored in that artifact directory
//
// Path safety: every resolved path stays beneath the repository root; writes are
// restricted to `docs/`; traversal and symlink escapes are rejected.

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { findManagedMarkers, replaceManagedInterior, normalizeManagedInteriors } = require("./docs-markers.js");

const OWNERS = {
  "commands": "prompts",
  "research-commands": "prompts",
  "release-notes": "release-generator",
};

function usage() {
  console.error(`Usage: node scripts/rebuild-docs.js [--root <path>] [--check] [--all] [--verify-fingerprint <metadata>] [--verify-artifact <directory>]`);
  process.exit(2);
}

function parseArgs(argv) {
  const args = { root: process.cwd(), check: false, all: false, verifyFingerprint: null, verifyArtifact: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") args.root = path.resolve(argv[++i]);
    else if (a === "--check") args.check = true;
    else if (a === "--all") args.all = true;
    else if (a === "--verify-fingerprint") args.verifyFingerprint = path.resolve(argv[++i]);
    else if (a === "--verify-artifact") args.verifyArtifact = path.resolve(argv[++i]);
    else return null;
  }
  return args;
}

function fail(message) {
  console.error(`rebuild-docs: ${message}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Path safety
// ---------------------------------------------------------------------------

function resolveInside(root, rel) {
  const target = path.resolve(root, rel);
  const rootResolved = fs.realpathSync(root);
  let realTarget;
  try {
    realTarget = fs.realpathSync(target);
  } catch (err) {
    if (err.code === "ENOENT") {
      let probe = target;
      const missing = [];
      while (!fs.existsSync(probe)) {
        missing.unshift(path.basename(probe));
        probe = path.dirname(probe);
      }
      realTarget = path.join(fs.realpathSync(probe), ...missing);
    } else {
      fail(`cannot resolve ${rel}: ${err.message}`);
    }
  }
  const relPath = path.relative(rootResolved, realTarget);
  if (relPath.startsWith("..") || path.isAbsolute(relPath)) {
    fail(`path escapes repository root: ${rel}`);
  }
  const out = path.resolve(rootResolved, relPath);
  const docsRel = path.relative(path.join(rootResolved, "docs"), out);
  if (docsRel.startsWith("..") || path.isAbsolute(docsRel)) {
    fail(`write target outside docs/: ${rel}`);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Minimal manifest parsing (ownership subset only)
// ---------------------------------------------------------------------------

function parseWikiManifest(manifestPath) {
  const text = fs.readFileSync(manifestPath, "utf8");
  if (!/schemaVersion\s*:\s*["']?compound-gpid-wiki-v1["']?/.test(text)) {
    fail(`wiki manifest schema version mismatch: ${manifestPath}`);
  }
  // file: entries must be plain filenames (no traversal or slashes).
  const fileRe = /^\s*file:\s*["']?(.+?)["']?\s*$/gm;
  let fm;
  while ((fm = fileRe.exec(text))) {
    if (fm[1].includes("..") || fm[1].includes("/") || fm[1].includes("\\")) {
      fail(`traversal rejected in wiki manifest page file: ${fm[1]}`);
    }
  }
  const pages = [];
  const blocks = text.split(/\n(?=\s{2}- id:)/).filter((b) => /- id:/.test(b));
  const ids = new Set();
  const orders = new Set();
  for (const block of blocks) {
    const id = /- id:\s*["']?([a-z0-9-]+)["']?/.exec(block)[1];
    if (ids.has(id)) fail(`duplicate page id '${id}' in wiki manifest`);
    ids.add(id);
    const file = /file:\s*["']?([^"'\s]+)["']?/.exec(block)[1];
    const ownership = /ownership:\s*["']?(\w+)["']?/.exec(block);
    if (ownership && !["auto", "manual"].includes(ownership[1])) {
      fail(`invalid ownership '${ownership[1]}' for wiki page '${id}'`);
    }
    const order = /order:\s*(\d+)/.exec(block);
    if (order) {
      if (orders.has(Number(order[1]))) fail(`duplicate page order ${order[1]} in wiki manifest`);
      orders.add(Number(order[1]));
    }
    // Sections only for auto-owned pages with a `sections:` block.
    const sections = [];
    const secMatch = block.match(/sections:([\s\S]*)$/);
    if (secMatch) {
      const secRe = /^\s*- id:\s*["']?([a-z0-9-]+)["']?/gm;
      let sm;
      while ((sm = secRe.exec(secMatch[1]))) sections.push(sm[1]);
    }
    pages.push({
      id,
      file,
      ownership: ownership ? ownership[1] : "manual",
      order: order ? Number(order[1]) : null,
      sections,
    });
  }
  return pages;
}

function replaceInterior(text, section, content) {
  try {
    return replaceManagedInterior(text, section, content);
  } catch (err) {
    fail(err.message);
  }
}

// ---------------------------------------------------------------------------
// Command table generation from canonical frontmatter
// ---------------------------------------------------------------------------

function escapeCell(value) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\r\n/g, "\n").replace(/<br>/g, " ").replace(/\n/g, "<br>").replace(/\|/g, "\\|");
}

function promptDescription(filePath) {
  let text = fs.readFileSync(filePath, "utf8");
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) fail(`prompt ${path.basename(filePath)} has no frontmatter`);
  const lines = m[1].split(/\r?\n/);
  const descriptionAt = lines.findIndex((line) => /^description:\s*/.test(line));
  if (descriptionAt === -1) fail(`prompt ${path.basename(filePath)} is missing required description frontmatter`);
  const rawValue = lines[descriptionAt].replace(/^description:\s*/, "").trim();
  if (!rawValue) fail(`prompt ${path.basename(filePath)} has an empty description frontmatter`);
  if (/^["']/.test(rawValue) && !rawValue.endsWith(rawValue[0])) {
    const quote = rawValue[0];
    const parts = [rawValue.slice(1)];
    let closed = false;
    for (let i = descriptionAt + 1; i < lines.length; i++) {
      if (!/^\s+/.test(lines[i])) break;
      const part = lines[i].trim();
      if (part.endsWith(quote)) {
        parts.push(part.slice(0, -1));
        closed = true;
        break;
      }
      parts.push(part);
    }
    if (!closed) fail(`prompt ${path.basename(filePath)} has an unterminated description frontmatter`);
    return parts.join(" ").trim();
  }
  if (/^[>|]/.test(rawValue)) {
    const folded = rawValue.startsWith(">");
    const parts = [];
    for (let i = descriptionAt + 1; i < lines.length; i++) {
      if (!/^\s+/.test(lines[i])) break;
      const part = lines[i].trim();
      if (part) parts.push(part);
    }
    if (parts.length === 0) fail(`prompt ${path.basename(filePath)} has an empty description frontmatter`);
    return parts.join(folded ? " " : "\n");
  }
  const quoted = rawValue.match(/^(["'])([\s\S]*)\1$/);
  return (quoted ? quoted[2] : rawValue).trim();
}

function generateCommandTable(root, prefix) {
  const promptsDir = path.join(root, ".github", "prompts");
  if (!fs.existsSync(promptsDir)) fail(`canonical prompts directory missing: ${promptsDir}`);
  const files = fs.readdirSync(promptsDir)
    .filter((f) => f.startsWith(prefix) && f.endsWith(".prompt.md"))
    .sort();
  if (files.length === 0) fail(`no canonical '${prefix}*.prompt.md' prompts found`);
  const rows = files.map((file) => {
    const command = `/${path.basename(file, ".prompt.md")}`;
    return `| \`${command}\` | Copilot model picker | ${escapeCell(promptDescription(path.join(promptsDir, file)))} |`;
  });
  return `| Prompt | Model | Purpose |\n|--------|-------|---------|\n${rows.join("\n")}\n`;
}

// ---------------------------------------------------------------------------
// Canonical-input fingerprint (normalized docs source)
// ---------------------------------------------------------------------------

function collectFiles(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...collectFiles(full));
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function normalizeText(text) {
  return normalizeManagedInteriors(text);
}

function docsSource(root) {
  const out = [];
  const docsDir = path.join(root, "docs");
  if (fs.existsSync(docsDir)) {
    for (const f of collectFiles(docsDir)) {
      const rel = path.relative(root, f).split(path.sep).join("/");
      out.push(`D:${rel}\n${normalizeText(fs.readFileSync(f, "utf8"))}`);
    }
  }
  return out.sort().join("\n");
}

function canonicalInputFingerprint(root) {
  const hash = crypto.createHash("sha256");
  const parts = [];
  const dirInputs = [
    [".github/prompts", ".md"],
    [".github/skills", ".md"],
    [".github/agents", ".md"],
    ["releases", ".json"],
  ];
  for (const [dir, ext] of dirInputs) {
    const full = path.join(root, dir);
    if (!fs.existsSync(full)) continue;
    for (const f of collectFiles(full).sort()) {
      if (!f.endsWith(ext) || path.basename(f) === ".gitkeep") continue;
      const rel = path.relative(root, f).split(path.sep).join("/");
      parts.push(`F:${rel}\n${fs.readFileSync(f, "utf8")}`);
    }
  }
  for (const rel of [
    "scripts/rebuild-docs.js",
    "scripts/generate-whats-new.js",
    "scripts/docs-markers.js",
    "scripts/check-docs-site.js",
    ".github/workflows/doc-rebuild.yml",
    ".github/workflows/pages.yml",
    ".github/workflows/release-docs.yml",
    ".github/workflows/release-pages.yml",
  ]) {
    const full = path.join(root, rel);
    if (fs.existsSync(full)) parts.push(`F:${rel}\n${fs.readFileSync(full, "utf8")}`);
  }
  parts.push(docsSource(root));
  const joined = parts.sort().join("\n");
  hash.update(joined);
  return { fingerprint: hash.digest("hex") };
}

function perFileDigests(root) {
  const digests = {};
  const docsDir = path.join(root, "docs");
  if (fs.existsSync(docsDir)) {
    for (const f of collectFiles(docsDir).sort()) {
      const rel = path.relative(docsDir, f).split(path.sep).join("/");
      digests[rel] = crypto.createHash("sha256").update(fs.readFileSync(f)).digest("hex");
    }
  }
  return digests;
}

// ---------------------------------------------------------------------------
// Rebuild driver
// ---------------------------------------------------------------------------

function readBuildMetadata(metaPath) {
  if (!fs.existsSync(metaPath)) fail(`build metadata missing: ${metaPath}`);
  try {
    const meta = JSON.parse(fs.readFileSync(metaPath, "utf8"));
    if (meta.schemaVersion !== 1 || !meta.site || typeof meta.site.fingerprint !== "string"
      || !meta.site.files || typeof meta.site.files !== "object") {
      fail(`build metadata has an invalid schema: ${metaPath}`);
    }
    return meta;
  } catch (err) {
    if (err && /^rebuild-docs:/.test(err.message)) throw err;
    fail(`build metadata is not valid JSON: ${metaPath}`);
  }
}

function verifyArtifact(artifactDir) {
  const meta = readBuildMetadata(path.join(artifactDir, ".docs-build-metadata.json"));
  const artifactDocs = path.join(artifactDir, "docs");
  if (!fs.existsSync(artifactDocs)) fail(`artifact docs directory missing: ${artifactDocs}`);
  const actual = perFileDigests(artifactDir);
  const expected = meta.site.files;
  const expectedPaths = Object.keys(expected).sort();
  const actualPaths = Object.keys(actual).sort();
  if (expectedPaths.join("\n") !== actualPaths.join("\n")) {
    fail("artifact file list does not match build metadata");
  }
  for (const rel of expectedPaths) {
    if (actual[rel] !== expected[rel]) fail(`artifact digest mismatch: docs/${rel}`);
  }
  console.log("rebuild-docs: artifact digests current");
  return 0;
}

function runRebuild(root, { check = false, all = false, verifyFingerprint = null, verifyArtifact: artifactDir = null } = {}) {
  if (artifactDir) return verifyArtifact(artifactDir);
  resolveInside(root, "docs/_wiki.yml");
  const manifestPath = path.join(root, "docs", "_wiki.yml");
  if (!fs.existsSync(manifestPath)) fail(`wiki manifest missing: ${manifestPath}`);
  const pages = parseWikiManifest(manifestPath);

  for (const page of pages) {
    if (page.ownership !== "auto") continue;
    const target = resolveInside(root, path.join("docs", page.file));
    const docsDir = fs.realpathSync(path.join(root, "docs"));
    if (path.dirname(target) !== docsDir) fail(`auto page '${page.id}' must live in docs/ root`);
    for (const section of page.sections) {
      if (!OWNERS[section]) fail(`declared managed section '${section}' on '${page.id}' has no recognized owner`);
    }
    let markers;
    try {
      markers = findManagedMarkers(fs.readFileSync(target, "utf8"));
    } catch (err) {
      fail(err.message);
    }
    const markerSections = markers.map((marker) => marker.section);
    if (new Set(markerSections).size !== markerSections.length) {
      fail(`auto page '${page.id}' declares a duplicate cg:auto marker`);
    }
    if (markerSections.length !== page.sections.length
      || markerSections.some((section) => !page.sections.includes(section))
      || page.sections.some((section) => !markerSections.includes(section))) {
      fail(`auto page '${page.id}' markers do not match declared managed sections`);
    }
  }

  const reference = pages.find((p) => p.file === "reference.md");
  if (!reference) fail("wiki manifest has no reference.md page");
  const refPath = path.join(root, "docs", "reference.md");
  let refText = fs.readFileSync(refPath, "utf8");
  let markers;
  try {
    markers = findManagedMarkers(refText);
  } catch (err) {
    fail(err.message);
  }
  const declaredRef = new Set(reference.sections);
  for (const mk of markers) {
    const inManifest = reference.sections.includes(mk.section);
    const inOwner = OWNERS[mk.section];
    if (!inManifest && !inOwner) {
      fail(`marker '${mk.section}' in reference.md is not declared in the wiki manifest`);
    }
    if (!inOwner) {
      fail(`marker '${mk.section}' in reference.md has no recognized owner`);
    }
  }

  let changed = false;
  const tables = {
    "commands": generateCommandTable(root, "cg-"),
    "research-commands": generateCommandTable(root, "cr-"),
  };
  for (const section of Object.keys(tables)) {
    const next = replaceInterior(refText, section, tables[section]);
    if (next !== refText) { changed = true; refText = next; }
  }

  if (verifyFingerprint) {
    const meta = readBuildMetadata(verifyFingerprint);
    const current = canonicalInputFingerprint(root);
    if (current.fingerprint === meta.site.fingerprint) {
      console.log("rebuild-docs: fingerprint current");
      return 0;
    }
    console.log("rebuild-docs: fingerprint stale (newer canonical inputs than the rebuild run)");
    return 1;
  }

  const whatsNew = all ? require("./generate-whats-new.js") : null;
  const releaseBuild = all ? whatsNew.prepareReleaseNotes(root) : null;

  if (all) {
    // Build and validate the release page before writing either managed page,
    // so malformed payloads cannot leave a partial documentation render.
    if (check) {
      const stale = [];
      if (changed) stale.push("docs/reference.md");
      if (releaseBuild.changed) stale.push("docs/whats-new.md");
      if (stale.length) {
        console.log(stale.join("\n"));
        return 1;
      }
      console.log("rebuild-docs: complete build current");
      return 0;
    }
    if (changed) fs.writeFileSync(refPath, refText);
    if (releaseBuild.changed) fs.writeFileSync(releaseBuild.filePath, releaseBuild.next);
    const meta = {
      schemaVersion: 1,
      version: "1",
      site: {
        fingerprint: canonicalInputFingerprint(root).fingerprint,
        files: perFileDigests(root),
      },
    };
    const metaPath = path.join(root, ".docs-build-metadata.json");
    fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2) + "\n");
    if (changed || releaseBuild.changed) console.log("rebuild-docs: --all rebuilt managed documentation");
    else console.log("rebuild-docs: --all current (no changes)");
    return 0;
  }

  if (!check && changed) fs.writeFileSync(refPath, refText);

  if (check) {
    const stale = [];
    if (changed) stale.push("docs/reference.md");
    if (stale.length) {
      console.log(stale.join("\n"));
      return 1;
    }
    console.log("rebuild-docs: current");
    return 0;
  }

  if (changed) console.log("rebuild-docs: updated docs/reference.md");
  else console.log("rebuild-docs: current (no changes)");
  return 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) usage();
  try {
    const code = runRebuild(args.root, args);
    process.exitCode = code;
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    if (!/^rebuild-docs:/.test(msg)) console.error(`rebuild-docs: ${msg}`);
    else console.error(msg);
    process.exitCode = 1;
  }
}

if (require.main === module) main();

module.exports = { runRebuild, canonicalInputFingerprint, perFileDigests, normalizeText, verifyArtifact };
