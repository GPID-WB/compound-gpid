"use strict";
// Protected paired-site generation: canonical data, expected builds and final output stay separate.
const fs = require("node:fs");
const path = require("node:path");
const source = require("./docs-source.js");
const contract = require("./docs-build-contract.js");
const provenance = require("./docs-provenance.js");
const { fingerprint } = require("./docs-fingerprint.js");
const DEV_MARKER = '<div class="dev-preview-banner" role="status">Development preview built from <code>dev</code>. It may change before release.</div>';
// Captured 9afd40ef and current main e6b19fbe use the same heading/router rules;
// only navigation construction/validation differs. No capability is guessed.
const LEGACY_RUNTIMES = new Set([
  "b935a77c9ef3e10f8153f4ac564ac7c1bd261864f4ad15b5b4245b2efd6117f4",
  "1ac35e0d905870e8cc8d8f6a5990c6542790f65db3f8af0d96e150d50bfd8f1a",
]);
const fail = message => { throw Error(`docs-channel-build: ${message}`); };
const json = value => Buffer.from(JSON.stringify(value, null, 2) + "\n");

/** True only for the new shell template; unknown producer versions still fail identification. */
function upgraded(root) {
  return fs.readFileSync(path.join(root, "docs/index.html"), "utf8").includes('name="cg-docs-shell"');
}
function replaceOnce(text, before, after) {
  if (text.split(before).length !== 2) fail(`missing or repeated owned shell slot: ${before}`);
  return text.replace(before, after);
}

/** Compute exact stamp/asset/banner transforms from independently established channel bytes. */
function channel(root, name, identity, artifact) {
  let producer, files;
  const canonical = source.readTree(path.join(root, "docs"));
  contract.assertSourcePaths([...canonical.keys()]);
  if (upgraded(root)) {
    producer = provenance.identifyProducer(root);
    if (producer.fingerprintVersion < 2) fail("upgraded shell requires its matching producer");
    files = artifact ? provenance.verifyProducer(root, artifact).files : provenance.expectedDocs(root, producer);
  } else {
    producer = contract.producers["compound-gpid-docs-producer-v1"];
    if (!LEGACY_RUNTIMES.has(source.hash(canonical.get("assets/site.js") || ""))) fail("unknown legacy runtime");
    // Tagged legacy builds generated managed sections; branch-root pages preserve
    // committed bytes. Recovery repeats that distinction from the trusted ref.
    files = artifact ? provenance.verifyProducer(root, artifact).files :
      identity.tag ? provenance.expectedDocs(root, provenance.identifyProducer(root)) : canonical;
  }
  files = new Map(files);
  const record = { path: name === "published" ? "" : "dev/", source: identity, ...producer,
    fingerprint: fingerprint(root, producer.fingerprintVersion), files: {}, shellBuildId: null, assets: [] };
  let html = files.get("index.html").toString("utf8");
  if (producer.fingerprintVersion >= 2) {
    record.shellBuildId = contract.shellBuildId(record);
    html = replaceOnce(html, 'content="__CG_DOCS_SHELL_BUILD_ID__"', `content="${record.shellBuildId}"`);
    for (const file of contract.assetSources(producer.fingerprintVersion)) {
      let bytes = files.get(file);
      if (!bytes) fail(`missing shell asset ${file}`);
      if (file === "assets/site.js") bytes = Buffer.from(replaceOnce(bytes.toString("utf8"),
        '"__CG_DOCS_SHELL_BUILD_ID__"', JSON.stringify(record.shellBuildId)));
      const sha256 = source.hash(bytes), output = file.replace(/\.(js|css)$/, `.${sha256}.$1`);
      const integrity = `sha256-${Buffer.from(sha256, "hex").toString("base64")}`;
      files.set(output, bytes); record.assets.push({ source: file, path: output, sha256, integrity });
      const attr = file.endsWith(".css") ? "href" : "src";
      html = replaceOnce(html, `${attr}="${file}"`, `${attr}="${output}" integrity="${integrity}" crossorigin="anonymous"`);
    }
  }
  if (name === "development") {
    if (html.includes("dev-preview-banner")) fail("existing development banner");
    html = replaceOnce(html, "<body>", `<body>${DEV_MARKER}`);
  }
  files.set("index.html", Buffer.from(html)); record.files = source.digests(files);
  return { record, files };
}

/** Build exact two-channel output; optional artifacts are independently validated, never source replacements. */
function expectedPair(options) {
  const { mainRoot, devRoot, mainSha, devSha } = options;
  const mainIdentity = { sha: mainSha, branch: options.mainBranch || "main", ref: options.mainRef || "main" };
  if (mainIdentity.ref.startsWith("v")) {
    require("./release-version.js").parseReleaseTag(mainIdentity.ref);
    mainIdentity.tag = mainIdentity.ref;
  }
  const main = channel(mainRoot, "published", mainIdentity, options.mainBuild);
  const dev = channel(devRoot, "development", { sha: devSha, branch: options.devBranch || "dev", ref: options.devRef || "dev" }, options.devBuild);
  const channels = { schemaVersion: "compound-gpid-docs-channels-v1", channels: { published: main.record, development: dev.record } };
  // The unpublished v2 checkpoint cannot parse v3 metadata. Keep its recovery
  // artifact intact; never declare working identity controls for a mixed pair.
  const versions = [main.record.fingerprintVersion, dev.record.fingerprintVersion];
  if (versions.includes(2) && versions.includes(3)) fail("historical v2 recovery cannot be paired with v3; rebuild both upgraded channels with v3");
  contract.validateChannels(channels);
  const files = new Map([...main.files, ...[...dev.files].map(([n, v]) => [`dev/${n}`, v])]);
  files.set("channels.json", json(channels));
  return { files, channels };
}

/** Write only verified output, after checking output/source overlap. */
function assemble(options) {
  source.separate(options.out, [options.mainRoot, options.devRoot, options.mainBuild, options.devBuild].filter(Boolean));
  const { files, channels } = expectedPair(options);
  const metadata = { schemaVersion: 2, version: "2", sources: {
    main: { ...channels.channels.published.source, fingerprint: channels.channels.published.fingerprint },
    dev: { ...channels.channels.development.source, fingerprint: channels.channels.development.fingerprint },
  }, site: { files: source.digests(files) } };
  const output = new Map([...files].map(([n, v]) => [`site/${n}`, v]));
  output.set(".docs-build-metadata.json", json(metadata));
  source.writeTree(options.out, output, [options.mainRoot, options.devRoot]);
  return 0;
}

/** Recompute paired metadata and every permitted transform from unchanged canonical inputs. */
function verify(artifact, mainRoot, devRoot, identity = {}) {
  if (!mainRoot || !devRoot) fail("both canonical source roots required for v2 verification");
  const inventory = source.readTree(artifact);
  if ([...inventory.keys()].some(n => n !== ".docs-build-metadata.json" && !n.startsWith("site/"))) fail("unexpected artifact inventory");
  const metadata = JSON.parse(inventory.get(".docs-build-metadata.json"));
  if (metadata.schemaVersion !== 2 || metadata.version !== "2") fail("unknown paired artifact contract");
  const options = { mainRoot, devRoot };
  for (const name of ["main", "dev"]) {
    const row = metadata.sources?.[name];
    if (!row) fail("missing source identity");
    for (const field of ["sha", "branch", "ref"]) {
      const key = name + field[0].toUpperCase() + field.slice(1);
      if (identity[key] && identity[key] !== row[field]) fail("source identity mismatch");
      options[key] = identity[key] || row[field];
    }
  }
  const expected = expectedPair(options), actual = new Map([...inventory].filter(([n]) => n.startsWith("site/")).map(([n, v]) => [n.slice(5), v]));
  for (const name of ["main", "dev"]) {
    const row = expected.channels.channels[name === "main" ? "published" : "development"];
    if (metadata.sources[name].fingerprint !== row.fingerprint) fail("canonical source fingerprint is stale");
  }
  source.equalFiles(actual, expected.files, "paired output");
  if (JSON.stringify(metadata.site?.files) !== JSON.stringify(source.digests(actual))) fail("final artifact digest mismatch");
  return 0;
}
module.exports = { upgraded, channel, expectedPair, assemble, verify, LEGACY_RUNTIMES };
