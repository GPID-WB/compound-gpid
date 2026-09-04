"use strict";
// Created 2026-09-03.

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { canonicalInputFingerprint } = require("./rebuild-docs.js");

const REQUIRED_SITE_FILES = [
  "index.html",
  "navigation.json",
  "assets/site.css",
  "assets/site.js",
  ".nojekyll",
];
const SHA_PATTERN = /^[0-9a-f]{40}$/i;
const METADATA_FILE = ".docs-build-metadata.json";
const SITE_DIRECTORY = "site";
const DEV_MARKER = "<div class=\"dev-preview-banner\" role=\"status\">Development preview built from <code>dev</code>. It may change before release.</div>";

function fail(message) {
  throw new Error(`assemble-docs-site: ${message}`);
}

function usage() {
  console.error("Usage: node scripts/assemble-docs-site.js --main-root <path> --dev-root <path> --out <path> --main-sha <sha> --dev-sha <sha>");
  console.error("       node scripts/assemble-docs-site.js --verify <artifact-dir> [--main-root <path>] [--dev-root <path>]");
  process.exitCode = 2;
}

function parseArgs(argv) {
  const args = {
    mainRoot: null,
    devRoot: null,
    out: null,
    mainSha: null,
    devSha: null,
    mainBranch: null,
    devBranch: null,
    mainRef: null,
    devRef: null,
    verify: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--main-root") args.mainRoot = path.resolve(argv[++index]);
    else if (argument === "--dev-root") args.devRoot = path.resolve(argv[++index]);
    else if (argument === "--out") args.out = path.resolve(argv[++index]);
    else if (argument === "--main-sha") args.mainSha = argv[++index];
    else if (argument === "--dev-sha") args.devSha = argv[++index];
    else if (argument === "--main-branch") args.mainBranch = argv[++index];
    else if (argument === "--dev-branch") args.devBranch = argv[++index];
    else if (argument === "--main-ref") args.mainRef = argv[++index];
    else if (argument === "--dev-ref") args.devRef = argv[++index];
    else if (argument === "--verify") args.verify = path.resolve(argv[++index]);
    else return null;
  }
  return args;
}

function assertDirectory(directory, label) {
  if (!fs.existsSync(directory)) fail(`${label} is missing: ${directory}`);
  const stat = fs.lstatSync(directory);
  if (stat.isSymbolicLink()) fail(`${label} must not be a symbolic link: ${directory}`);
  if (!stat.isDirectory()) fail(`${label} is not a directory: ${directory}`);
}

function regularFiles(directory) {
  assertDirectory(directory, "source directory");
  const files = [];
  function walk(current, prefix = "") {
    const entries = fs.readdirSync(current, { withFileTypes: true })
      .sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      const relative = path.join(prefix, entry.name).split(path.sep).join("/");
      const full = path.join(current, entry.name);
      if (entry.isSymbolicLink()) fail(`symbolic links are not allowed: ${relative}`);
      if (entry.isDirectory()) walk(full, relative);
      else if (entry.isFile()) files.push({ full, relative });
      else fail(`unsupported filesystem entry: ${relative}`);
    }
  }
  walk(directory);
  return files;
}

function sourceTree(root, label) {
  const docs = path.join(root, "docs");
  assertDirectory(root, `${label} source root`);
  assertDirectory(docs, `${label} docs root`);
  const files = regularFiles(docs);
  const names = new Set(files.map((file) => file.relative));
  for (const required of REQUIRED_SITE_FILES) {
    if (!names.has(required)) fail(`${label} docs tree is missing ${required}`);
  }
  return { root, docs, files };
}

function digest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function digestTree(directory) {
  const digests = {};
  for (const file of regularFiles(directory)) digests[file.relative] = digest(file.full);
  return digests;
}

function ensureSafeRelative(relative) {
  if (!relative || relative.startsWith("/") || relative.includes("../") || relative.includes("\\")) {
    fail(`unsafe output path: ${relative}`);
  }
}

function copyFile(source, destination) {
  ensureSafeRelative(path.relative(path.dirname(destination), destination));
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(source, destination);
}

function addDevelopmentMarker(file) {
  let content = fs.readFileSync(file, "utf8");
  if (content.includes("dev-preview-banner") || content.includes("Development preview built from")) {
    fail("dev index already contains a development marker");
  }
  const body = content.search(/<body(?:\s[^>]*)?>/i);
  if (body === -1) fail("dev index.html has no body element");
  const bodyEnd = content.indexOf(">", body);
  content = `${content.slice(0, bodyEnd + 1)}\n    ${DEV_MARKER}\n${content.slice(bodyEnd + 1)}`;
  fs.writeFileSync(file, content);
}

function copySource(source, destination, prefix, occupied) {
  for (const file of source.files) {
    if (prefix === "" && file.relative === "dev/index.html") {
      fail("stable docs already contain the reserved dev/ preview path");
    }
    const relative = prefix ? `${prefix}/${file.relative}` : file.relative;
    ensureSafeRelative(relative);
    if (occupied.has(relative)) fail(`output path collision: ${relative}`);
    occupied.add(relative);
    const destinationFile = path.join(destination, relative);
    copyFile(file.full, destinationFile);
  }
}

function validateSha(value, label) {
  if (!SHA_PATTERN.test(value || "")) fail(`${label} must be a full 40-character commit SHA`);
}

function buildMetadata(mainRoot, devRoot, mainSha, devSha, mainBranch, devBranch, mainRef, devRef, siteDirectory) {
  return {
    schemaVersion: 1,
    version: "1",
    sources: {
      main: {
        branch: mainBranch,
        ref: mainRef,
        sha: mainSha,
        fingerprint: canonicalInputFingerprint(mainRoot).fingerprint,
      },
      dev: {
        branch: devBranch,
        ref: devRef,
        sha: devSha,
        fingerprint: canonicalInputFingerprint(devRoot).fingerprint,
      },
    },
    site: {
      files: digestTree(siteDirectory),
    },
  };
}

function writeCombinedSite({ mainRoot, devRoot, out, mainSha, devSha, mainBranch, devBranch, mainRef, devRef }) {
  validateSha(mainSha, "--main-sha");
  validateSha(devSha, "--dev-sha");
  const main = sourceTree(mainRoot, "main");
  const dev = sourceTree(devRoot, "dev");
  const output = path.resolve(out);
  const parent = path.dirname(output);
  fs.mkdirSync(parent, { recursive: true });
  const staging = fs.mkdtempSync(path.join(parent, `.${path.basename(output)}-staging-`));
  try {
    const site = path.join(staging, SITE_DIRECTORY);
    fs.mkdirSync(site, { recursive: true });
    const occupied = new Set();
    copySource(main, site, "", occupied);
    copySource(dev, site, "dev", occupied);
    addDevelopmentMarker(path.join(site, "dev", "index.html"));
    const metadata = buildMetadata(
      mainRoot,
      devRoot,
      mainSha,
      devSha,
      mainBranch || "main",
      devBranch || "dev",
      mainRef || "main",
      devRef || "dev",
      site,
    );
    fs.writeFileSync(path.join(staging, METADATA_FILE), `${JSON.stringify(metadata, null, 2)}\n`);
    if (fs.existsSync(output)) {
      const existing = fs.lstatSync(output);
      if (existing.isSymbolicLink()) fail(`output must not be a symbolic link: ${output}`);
      if (!existing.isDirectory()) fail(`output is not a directory: ${output}`);
      fs.rmSync(output, { recursive: true, force: true });
    }
    fs.renameSync(staging, output);
  } catch (error) {
    fs.rmSync(staging, { recursive: true, force: true });
    throw error;
  }
  console.log(`assemble-docs-site: wrote ${output}`);
  return 0;
}

function readMetadata(artifact) {
  const metadataPath = path.join(artifact, METADATA_FILE);
  if (!fs.existsSync(metadataPath)) fail(`metadata is missing: ${metadataPath}`);
  let metadata;
  try {
    metadata = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  } catch (error) {
    fail(`metadata is not valid JSON: ${error.message}`);
  }
  if (metadata.schemaVersion !== 1 || metadata.version !== "1" || !metadata.sources
    || !metadata.sources.main || !metadata.sources.dev || !metadata.site
    || !metadata.site.files || typeof metadata.site.files !== "object") {
    fail("metadata has an invalid schema");
  }
  for (const source of ["main", "dev"]) {
    if (typeof metadata.sources[source].branch !== "string" || !metadata.sources[source].branch
      || typeof metadata.sources[source].ref !== "string" || !metadata.sources[source].ref
      || !SHA_PATTERN.test(metadata.sources[source].sha || "")
      || typeof metadata.sources[source].fingerprint !== "string"
      || !metadata.sources[source].fingerprint) {
      fail(`metadata has an invalid ${source} source record`);
    }
  }
  return metadata;
}

function verifyCombinedSite(artifact, mainRoot = null, devRoot = null, expectedIdentity = {}) {
  assertDirectory(artifact, "artifact directory");
  const metadata = readMetadata(artifact);
  const site = path.join(artifact, SITE_DIRECTORY);
  assertDirectory(site, "combined site directory");
  const actual = digestTree(site);
  const expected = metadata.site.files;
  const expectedPaths = Object.keys(expected).sort();
  const actualPaths = Object.keys(actual).sort();
  if (expectedPaths.join("\n") !== actualPaths.join("\n")) {
    fail("combined site file list does not match metadata");
  }
  for (const relative of expectedPaths) {
    ensureSafeRelative(relative);
    if (actual[relative] !== expected[relative]) fail(`combined site digest mismatch: ${relative}`);
  }
  for (const required of REQUIRED_SITE_FILES) {
    if (!actual[required]) fail(`combined site is missing stable file: ${required}`);
    if (!actual[`dev/${required}`]) fail(`combined site is missing dev file: dev/${required}`);
  }
  const devIndex = fs.readFileSync(path.join(site, "dev", "index.html"), "utf8");
  const stableIndex = fs.readFileSync(path.join(site, "index.html"), "utf8");
  if (stableIndex.includes("dev-preview-banner") || stableIndex.includes("Development preview built from")) {
    fail("stable site contains the development marker");
  }
  if (!devIndex.includes("dev-preview-banner") || !devIndex.includes("Development preview built from")) {
    fail("combined site is missing the development marker");
  }
  for (const source of ["main", "dev"]) {
    const expectedBranch = expectedIdentity[`${source}Branch`];
    const expectedRef = expectedIdentity[`${source}Ref`];
    if (expectedBranch && metadata.sources[source].branch !== expectedBranch) {
      fail(`${source} source branch does not match expected identity`);
    }
    if (expectedRef && metadata.sources[source].ref !== expectedRef) {
      fail(`${source} source ref does not match expected identity`);
    }
  }
  if (mainRoot || devRoot) {
    if (!mainRoot || !devRoot) fail("both --main-root and --dev-root are required for source verification");
    const currentMain = canonicalInputFingerprint(path.resolve(mainRoot)).fingerprint;
    const currentDev = canonicalInputFingerprint(path.resolve(devRoot)).fingerprint;
    if (currentMain !== metadata.sources.main.fingerprint) fail("main source fingerprint is stale");
    if (currentDev !== metadata.sources.dev.fingerprint) fail("dev source fingerprint is stale");
    if (expectedIdentity.mainSha && metadata.sources.main.sha !== expectedIdentity.mainSha) fail("main source SHA does not match expected identity");
    if (expectedIdentity.devSha && metadata.sources.dev.sha !== expectedIdentity.devSha) fail("dev source SHA does not match expected identity");
  }
  console.log("assemble-docs-site: combined artifact is current");
  return 0;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args) return usage();
  try {
    if (args.verify) {
      return verifyCombinedSite(args.verify, args.mainRoot, args.devRoot, {
        mainSha: args.mainSha,
        devSha: args.devSha,
        mainBranch: args.mainBranch,
        devBranch: args.devBranch,
        mainRef: args.mainRef,
        devRef: args.devRef,
      });
    }
    if (!args.mainRoot || !args.devRoot || !args.out || !args.mainSha || !args.devSha) return usage();
    return writeCombinedSite(args);
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    console.error(message.startsWith("assemble-docs-site:") ? message : `assemble-docs-site: ${message}`);
    process.exitCode = 1;
    return 1;
  }
}

if (require.main === module) main();

module.exports = { writeCombinedSite, verifyCombinedSite, digestTree };