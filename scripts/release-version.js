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

/** Validate a Git branch as data, never as a ref expression or command option. */
function validBranch(branch) {
  return typeof branch === "string" && branch.length > 0 && branch.length <= 1024 &&
    !branch.startsWith("-") && !branch.endsWith(".") && !/[\x00-\x20\x7f~^:?*\[\\]/.test(branch) &&
    !branch.includes("..") && !branch.includes("@{") &&
    branch.split("/").every(part => part && !part.startsWith(".") && !part.endsWith(".lock"));
}

/** Check source eligibility; callers must separately verify remote branch/commit identity. */
function assertReleaseSource(tag, branch, defaultBranch, policy) {
  // Preserve the boundary with the separately authorized async controller.
  legacyDocsBranch(tag);
  if (!validBranch(branch) || !validBranch(defaultBranch)) throw new Error("Invalid release source branch");
  const production = policy?.production_branches === undefined ? [] : policy.production_branches;
  if (!Array.isArray(production) || !production.every(validBranch)) throw new Error("Invalid production_branches policy");
  if (!parseReleaseTag(tag).legacy && branch !== defaultBranch && !production.includes(branch)) {
    throw new Error("Stable release source branch is neither a configured deployment branch nor the remote default");
  }
  return branch;
}

/** Resolve a tag's eligible, current same-repository source by read-only GitHub evidence.
 * Example: resolveReleaseSource(process.env); RELEASE_SOURCE_BRANCH can pin a candidate.
 * A tag event has no originating branch. Without an explicit candidate, select a
 * permitted branch containing the exact commit, never infer one from tag shape.
 */
function resolveReleaseSource(env, transport = require("node:child_process").execFileSync) {
  const slug = env.GITHUB_REPOSITORY, repoId = Number(env.GITHUB_REPOSITORY_ID);
  const tag = env.RELEASE_TAG, sha = env.RELEASE_SHA;
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(slug) || !Number.isSafeInteger(repoId) || repoId <= 0 ||
      !/^[0-9a-f]{40}$/.test(sha)) throw new Error("Invalid release source identity");
  legacyDocsBranch(tag);
  const base = `repos/${slug}`;
  function get(endpoint, optional = false) {
    let raw, failed = false;
    try {
      raw = transport("gh", ["api", "--method", "GET", "--hostname", "github.com", "--include", endpoint],
        {encoding: "utf8", timeout: 20000, maxBuffer: 4194304, stdio: ["ignore", "pipe", "pipe"]});
    } catch (error) { failed = true; raw = error.stdout; }
    if (!raw || raw.length > 4194304) throw new Error("Bounded release source read failed");
    const text = raw.toString().replace(/\r\n/g, "\n");
    const split = text.indexOf("\n\n"), status = text.match(/^HTTP\/[\d.]+ (\d{3})\b/);
    if (split < 0 || !status) throw new Error("Unverifiable release source response");
    if (optional && status[1] === "404") return null;
    if (failed || status[1] !== "200") throw new Error("Release source read failed");
    return JSON.parse(text.slice(split + 2));
  }
  const repo = get(base);
  if (repo.id !== repoId || repo.full_name !== slug || repo.fork !== false || !validBranch(repo.default_branch)) {
    throw new Error("Release source repository identity differs");
  }
  const defaultPath = `${base}/branches/${encodeURIComponent(repo.default_branch)}`;
  const controller = get(defaultPath);
  if (controller.name !== repo.default_branch || controller.protected !== true || !/^[0-9a-f]{40}$/.test(controller.commit?.sha)) {
    throw new Error("Release source requires protected default policy");
  }
  const document = get(`${base}/contents/.release-controller.json?ref=${controller.commit.sha}`, true);
  let policy = null;
  if (document !== null) {
    if (document.type !== "file" || document.encoding !== "base64" || typeof document.content !== "string" || document.content.length > 1048576) {
      throw new Error("Invalid remote source policy document");
    }
    const raw = Buffer.from(document.content, "base64").toString("utf8");
    const keys = [...raw.matchAll(/("(?:\\.|[^"\\])*")\s*:/g)].map(match => JSON.parse(match[1]));
    if (keys.filter(key => key === "enabled").length !== 1 || keys.filter(key => key === "production_branches").length > 1) {
      throw new Error("Ambiguous remote production_branches policy");
    }
    policy = JSON.parse(raw);
    if (typeof policy.enabled !== "boolean" || (policy.enabled && env.LEGACY_MODE !== "recovery")) throw new Error("Legacy source policy disabled after cutover");
  }
  assertReleaseSource(tag, repo.default_branch, repo.default_branch, policy);
  function fileBytes(file, commit) {
    const value = get(`${base}/contents/${file}?ref=${commit}`, true);
    if (value === null) return null;
    if (value.type !== "file" || value.encoding !== "base64" || typeof value.content !== "string" || value.content.length > 1048576) {
      throw new Error("Invalid release source payload document");
    }
    return Buffer.from(value.content, "base64");
  }
  const payload = fileBytes(`releases/${tag}.json`, sha);
  const taggedLatest = fileBytes("releases/latest.json", sha);
  if (!payload || !taggedLatest || !payload.equals(taggedLatest) || JSON.parse(payload).tag !== tag) {
    throw new Error("Exact release payload and tagged latest bytes are required");
  }
  let candidates;
  if (env.RELEASE_SOURCE_BRANCH) {
    candidates = [assertReleaseSource(tag, env.RELEASE_SOURCE_BRANCH, repo.default_branch, policy)];
  } else if (!parseReleaseTag(tag).legacy) {
    candidates = [...new Set([repo.default_branch, ...(policy?.production_branches || [])])];
  } else {
    candidates = [];
    const maxBranchPages = 20;
    for (let page = 1; page <= maxBranchPages; page++) {
      const branches = get(`${base}/branches?per_page=100&page=${page}`);
      if (!Array.isArray(branches) || branches.length > 100 || branches.some(branch => !validBranch(branch.name))) throw new Error("Invalid source branch inventory");
      candidates.push(...branches.map(branch => branch.name));
      if (branches.length < 100) break;
      if (page === maxBranchPages) throw new Error("Source branch inventory exceeds bound; supply RELEASE_SOURCE_BRANCH");
    }
    candidates = [...new Set(candidates)].sort();
  }
  for (const candidate of candidates) {
    const branchPath = `${base}/branches/${encodeURIComponent(candidate)}`;
    const branch = get(branchPath, true);
    if (branch === null) continue;
    if (branch.name !== candidate || !/^[0-9a-f]{40}$/.test(branch.commit?.sha)) throw new Error("Invalid remote source branch identity");
    assertReleaseSource(tag, candidate, repo.default_branch, policy);
    const comparison = get(`${base}/compare/${sha}...${branch.commit.sha}`);
    if (comparison.base_commit?.sha !== sha || comparison.merge_base_commit?.sha !== sha ||
        !["ahead", "identical"].includes(comparison.status)) continue;
    const candidateLatest = fileBytes("releases/latest.json", branch.commit.sha);
    if (!candidateLatest || !payload.equals(candidateLatest)) continue;
    const fresh = get(branchPath), freshDefault = get(defaultPath), freshRepo = get(base);
    if (fresh.name !== candidate || fresh.commit?.sha !== branch.commit.sha || freshDefault.name !== repo.default_branch ||
        freshDefault.protected !== true || freshDefault.commit?.sha !== controller.commit.sha ||
        freshRepo.id !== repoId || freshRepo.full_name !== slug || freshRepo.fork !== false || freshRepo.default_branch !== repo.default_branch) {
      throw new Error("Release source or protected policy changed during verification");
    }
    return candidate;
  }
  throw new Error("No eligible remote source branch contains the exact release commit and current payload");
}

module.exports = { parseReleaseTag, compareReleaseTags, legacyDocsBranch, assertReleaseSource, resolveReleaseSource };

if (require.main === module) {
  const fs = require("node:fs");
  const manifest = fs.existsSync(".release-manifest.json") ? JSON.parse(fs.readFileSync(".release-manifest.json", "utf8")) : null;
  if (process.argv.length === 3 && process.argv[2] === "--resolve-source") {
    legacyDocsBranch(process.env.RELEASE_TAG, manifest);
    process.stdout.write(resolveReleaseSource(process.env) + "\n");
  } else if (process.argv.length === 4 && process.argv[2] === "--full-site-tag") {
    legacyDocsBranch(process.argv[3], manifest);
    process.stdout.write(String(!parseReleaseTag(process.argv[3]).legacy) + "\n");
  } else if (process.argv.length === 4 && process.argv[2] === "--legacy-docs-branch") {
    process.stdout.write(legacyDocsBranch(process.argv[3], manifest) + "\n");
  } else throw new Error("Expected --resolve-source, --full-site-tag TAG, or --legacy-docs-branch TAG");
}
