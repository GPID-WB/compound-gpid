"use strict";

// Wire/transform contracts. Shape validation alone is not derivation proof
// or permission to publish; docs-provenance and docs-channel-build enforce it.
const crypto = require("node:crypto");
const SHA = /^[0-9a-f]{40}$/;
const DIGEST = /^[0-9a-f]{64}$/;
const PUBLIC_METADATA = "channels.json";
const ASSET_SOURCES = ["assets/site.js", "assets/site.css", "assets/docs-contract.js", "assets/docs-reading.js",
  "assets/docs-search.js", "assets/docs-tools.js", "assets/docs-identity.js"];
const producers = Object.freeze(Object.fromEntries([1, 2].map(version => [
  `compound-gpid-docs-producer-v${version}`, Object.freeze({
    producerContract: `compound-gpid-docs-producer-v${version}`, fingerprintVersion: version,
    runtimeContract: `compound-gpid-docs-runtime-v${version}`, headingContract: `compound-gpid-headings-v${version}`,
    capabilities: Object.freeze({ sectionLinks: true, redirectMappings: version === 2, switchNotices: version === 2,
      reverseSwitching: version === 2, verifiedIdentity: version === 2 }),
  }),
])));

// Input semantics are immutable within a version. V2 is not enabled in the
// protected rollout yet. A changed input/output algorithm requires another version.
const fingerprintContracts = Object.freeze({
  1: {
    implementationRevision: "9afd40ef4499da1b1cc9ade18e20ab596e4af6d2",
    generatorSha256: "d6e6c98ed6c1e318ee0b0aa5c462213279668a59411c7a1843aea7009d163a58",
    normalizerSha256: "527692c224e99258a92467935b4f6a1610d6b47206fd5f1aec80ddfb1e0ef432",
    normalization: "Exact legacy F:/D: transcript; sorted parts; raw UTF-8 and line endings; only managed doc interiors replaced.",
  },
  2: {
    directoryInputs: { ".github/prompts": [".md", ".help.json"], ".github/skills": [".md"], ".github/agents": [".md"], releases: [".json"] },
    fixedInputs: [".github/shared/module-registry.json", ".github/shared/help-catalog.json", ".github/shared/shell-commands.json",
      "scripts/rebuild-docs.js", "scripts/generate-whats-new.js", "scripts/release-payloads.js", "scripts/docs-markers.js",
      "scripts/check-docs-site.js", "scripts/assemble-docs-site.js", "scripts/legacy-pages.js", "scripts/docs-build-contract.js",
      "scripts/docs-source.js", "scripts/docs-provenance.js", "scripts/docs-fingerprint.js", "scripts/docs-channel-build.js", "scripts/docs-search-index.js",
      ".github/workflows/docs-site-build.yml", ".github/workflows/doc-rebuild.yml", ".github/workflows/pages.yml",
      ".github/workflows/release-docs.yml", ".github/workflows/release-pages.yml"],
    treeInputs: ["docs", "scripts/help", "scripts/docs-legacy-v1"],
    generatedOutputs: ["docs/assets/search-index.json", "docs/assets/command-index.json"],
    normalization: "UTF-8 with LF; managed Markdown interiors replaced with the v1 marker token; hash a sorted JSON array of [path, normalizedText] pairs.",
    absence: "Record [path, null] for each absent fixed input and absent input directory. Empty directories record [path, []].",
    exclusion: "Only the two exact generated outputs are excluded; each requires independent expected-byte verification. Stamped assets and channels.json are forbidden in source.",
  },
});

const transforms = Object.freeze([
  { id: "dev-banner-v1", output: "dev/index.html", operation: "Insert the exact DEV_MARKER immediately after the first body start tag; reject any existing marker." },
  { id: "shell-stamp-v2", outputs: ["index.html", "assets/site.js"], htmlSlot: 'content="__CG_DOCS_SHELL_BUILD_ID__"', runtimeSlot: '"__CG_DOCS_SHELL_BUILD_ID__"', operation: "Replace exactly one owned slot in each upgraded template with shellBuildId before hashing." },
  { id: "local-assets-v2", sources: ASSET_SOURCES, operation: "Emit assets/<stem>.<full-sha256>.<ext>; hash after stamping; replace exactly one source URL per HTML asset and add sha256 SRI; then hash final HTML." },
  { id: "channels-v1", output: PUBLIC_METADATA, operation: "Serialize independently verified channel records with JSON.stringify(value, null, 2) plus LF; include these bytes in final artifact digests, never in their own per-channel inputs." },
]);

const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const keys = (value, required, optional = []) => object(value) && required.every(key => Object.hasOwn(value, key))
  && Object.keys(value).every(key => required.includes(key) || optional.includes(key));
const fail = message => { throw new Error(`docs-build-contract: ${message}`); };
const safePath = value => typeof value === "string" && /^(?:\.nojekyll|[a-zA-Z0-9_-][a-zA-Z0-9_./-]*)$/.test(value)
  && value.split("/").every(part => part && part !== "." && part !== "..");
const digestMap = value => object(value) && Object.entries(value).every(([file, digest]) => safePath(file) && DIGEST.test(digest));

/** Select one known version after the protected caller identifies canonical code, never by trial. */
function selectProducer(metadata, canonicalContract, supported = Object.keys(producers)) {
  if (!object(metadata)) fail("invalid producer metadata");
  let name = metadata.producerContract;
  if (name === undefined && metadata.fingerprintVersion === undefined) {
    if (!keys(metadata, ["schemaVersion", "version", "site"]) || metadata.schemaVersion !== 1 || metadata.version !== "1"
      || !keys(metadata.site, ["fingerprint", "files"]) || !DIGEST.test(metadata.site.fingerprint) || !digestMap(metadata.site.files)) fail("unrecognized legacy metadata shape");
    name = "compound-gpid-docs-producer-v1";
  } else if (name === undefined || metadata.fingerprintVersion === undefined) fail("incomplete version declaration");
  if (!Object.hasOwn(producers, name)) fail("unknown producer contract");
  if (!supported.includes(name)) fail("unsupported producer contract on this controller");
  if (name !== canonicalContract) fail("producer does not match canonical code; downgrade forbidden");
  const selected = producers[name];
  if (metadata.fingerprintVersion !== undefined && metadata.fingerprintVersion !== selected.fingerprintVersion) fail("fingerprint version mismatch");
  return selected;
}

/** Reject exact composer-owned outputs, not broad JSON or generated-directory classes. */
function assertSourcePaths(paths) {
  for (const file of paths) {
    if (!safePath(file)) fail(`unsafe source path ${file}`);
    const folded = file.toLowerCase();
    if (folded === PUBLIC_METADATA || folded === "dev" || folded.startsWith("dev/")
      || /^assets\/(?:site|docs-(?:contract|reading|search|tools|identity))\.[0-9a-f]{64}\.(?:js|css)$/.test(folded)) fail(`reserved output path ${file}`);
  }
}

/** Deterministic pre-stamp identity; no stamped HTML or metadata participates in the hash. */
function shellBuildId(channel) {
  if (!SHA.test(channel.source?.sha) || !DIGEST.test(channel.fingerprint)
    || !Object.hasOwn(producers, channel.producerContract)) fail("invalid shell identity inputs");
  return crypto.createHash("sha256").update(JSON.stringify([
    channel.source.sha, channel.fingerprint, channel.producerContract,
    channel.fingerprintVersion, channel.runtimeContract, channel.headingContract,
  ])).digest("hex");
}

/** Validate the exact public channels.json shape. The caller must still prove every source/output byte. */
function validateChannels(metadata) {
  if (!keys(metadata, ["schemaVersion", "channels"]) || metadata.schemaVersion !== "compound-gpid-docs-channels-v1"
    || !keys(metadata.channels, ["published", "development"])) fail("invalid two-channel manifest");
  for (const [name, channel] of Object.entries(metadata.channels)) {
    if (!keys(channel, ["path", "source", "producerContract", "fingerprintVersion", "fingerprint", "runtimeContract", "headingContract", "capabilities", "files", "shellBuildId", "assets"])) fail(`invalid ${name} channel fields`);
    if (channel.path !== (name === "published" ? "" : "dev/")) fail("invalid channel path");
    if (!keys(channel.source, ["sha", "branch", "ref"], ["tag"]) || !SHA.test(channel.source.sha)
      || ![channel.source.branch, channel.source.ref].every(value => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(value) && !value.includes(".."))) fail("invalid source identity");
    if (name === "development" && (channel.source.branch !== "dev" || channel.source.ref !== "dev" || channel.source.tag !== undefined)) fail("development must identify dev");
    if (channel.source.tag !== undefined && (!/^v\d+\.\d+\.\d+(?:\.\d+)?$/.test(channel.source.tag) || channel.source.ref !== channel.source.tag)) fail("invalid source tag");
    const producer = selectProducer(channel, channel.producerContract);
    if (channel.runtimeContract !== producer.runtimeContract || channel.headingContract !== producer.headingContract) fail("unknown or mismatched runtime/heading contract");
    if (!keys(channel.capabilities, Object.keys(producer.capabilities))
      || Object.entries(producer.capabilities).some(([key, value]) => channel.capabilities[key] !== value)) fail("invalid channel capabilities");
    if (!DIGEST.test(channel.fingerprint) || !digestMap(channel.files)
      || Object.keys(channel.files).some(file => file.toLowerCase() === PUBLIC_METADATA || file.toLowerCase() === "dev" || file.toLowerCase().startsWith("dev/"))) fail("invalid channel digest map");
    for (const file of ["index.html", "navigation.json", "assets/site.js", "assets/site.css", ".nojekyll"]) {
      if (!Object.hasOwn(channel.files, file)) fail(`missing file digest ${file}`);
    }
    if (!Array.isArray(channel.assets)) fail("invalid asset inventory");
    if (producer.fingerprintVersion === 1) {
      if (channel.shellBuildId !== null || channel.assets.length) fail("legacy shell cannot claim a build stamp");
      continue;
    }
    if (channel.shellBuildId !== shellBuildId(channel)) fail("shell build identity mismatch");
    if (!Object.hasOwn(channel.files, "assets/docs-contract.js")) fail("missing canonical helper digest");
    if (channel.assets.length !== ASSET_SOURCES.length) fail("incomplete shell asset inventory");
    const seen = new Set();
    for (const asset of channel.assets) {
      if (!keys(asset, ["source", "path", "sha256", "integrity"]) || !ASSET_SOURCES.includes(asset.source)
        || seen.has(asset.source) || !DIGEST.test(asset.sha256)) fail("invalid shell asset inventory");
      seen.add(asset.source);
      if (asset.path !== asset.source.replace(/\.(js|css)$/, `.${asset.sha256}.$1`)
        || channel.files[asset.path] !== asset.sha256
        || asset.integrity !== `sha256-${Buffer.from(asset.sha256, "hex").toString("base64")}`) fail("asset path/digest/integrity mismatch");
    }
  }
  return metadata;
}

module.exports = { PUBLIC_METADATA, ASSET_SOURCES, producers, fingerprintContracts, transforms,
  selectProducer, assertSourcePaths, shellBuildId, validateChannels };
