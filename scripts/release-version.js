"use strict";

// Historical four-part identities stay separate from strict SemVer.
const number = "(?:0|[1-9][0-9]*)";
const identifier = "(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)";
const semver = new RegExp(`^v(${number})\\.(${number})\\.(${number})(?:-(${identifier}(?:\\.${identifier})*))?(?:\\+([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?$`);
const legacy = /^v([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$/;

function parseReleaseTag(tag) {
  if (typeof tag !== "string" || tag.length > 255 || /\s/.test(tag)) throw new Error("Unsupported release tag");
  const old = legacy.exec(tag);
  const match = old || semver.exec(tag);
  if (!match) throw new Error(`Unsupported release tag: ${tag}`);
  return { core: match.slice(1, 4).map(BigInt), legacy: Boolean(old),
    prerelease: old ? [match[4]] : (match[4] || "").split(".").filter(Boolean) };
}

function compareReleaseTags(left, right) {
  const a = parseReleaseTag(left), b = parseReleaseTag(right);
  const cmp = (x, y) => x < y ? -1 : x > y ? 1 : 0;
  for (let i = 0; i < 3; i++) {
    const result = cmp(a.core[i], b.core[i]);
    if (result) return result;
  }
  const lane = x => x.legacy ? 0 : x.prerelease.length ? 1 : 2;
  if (lane(a) !== lane(b)) return cmp(lane(a), lane(b));
  for (let i = 0; i < Math.max(a.prerelease.length, b.prerelease.length); i++) {
    const x = a.prerelease[i], y = b.prerelease[i];
    if (x === undefined || y === undefined) return cmp(a.prerelease.length, b.prerelease.length);
    const xn = /^[0-9]+$/.test(x), yn = /^[0-9]+$/.test(y);
    const result = xn && yn ? cmp(BigInt(x), BigInt(y)) : xn !== yn ? (xn ? -1 : 1) : cmp(x, y);
    if (result) return result;
  }
  return 0;
}

function legacyDocsBranch(tag, manifest = null) {
  const parsed = parseReleaseTag(tag);
  if ((manifest && manifest.tag === tag) || (!parsed.legacy && (parsed.prerelease.length || tag.includes("+"))))
    throw new Error("Controller-owned release: use registered immutable snapshots, not the legacy combined docs route");
  return parsed.legacy ? "dev" : "main";
}

module.exports = { parseReleaseTag, compareReleaseTags, legacyDocsBranch };

if (require.main === module) {
  const fs = require("node:fs");
  if (process.argv.length !== 4 || process.argv[2] !== "--legacy-docs-branch") throw new Error("Expected --legacy-docs-branch TAG");
  const manifest = fs.existsSync(".release-manifest.json") ? JSON.parse(fs.readFileSync(".release-manifest.json", "utf8")) : null;
  process.stdout.write(legacyDocsBranch(process.argv[3], manifest) + "\n");
}
