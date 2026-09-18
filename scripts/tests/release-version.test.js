"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const corpus = require("../../packages/cg-release/tests/fixtures/versions.json");
const { parseReleaseTag, compareReleaseTags } = require("../release-version.js");
const { legacyDocsBranch } = require("../release-version.js");
const { assertReleaseSource, resolveReleaseSource } = require("../release-version.js");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path");
const { loadReleasePayloads } = require("../generate-whats-new.js");

test("strict SemVer corpus, ASCII numeric order, and build identity", () => {
  for (const value of corpus.valid) assert.doesNotThrow(() => parseReleaseTag(`v${value}`));
  for (const value of corpus.invalid) assert.throws(() => parseReleaseTag(`v${value}`));
  const ascending = corpus.ascending.map(v => `v${v}`);
  assert.deepEqual([...ascending].reverse().sort(compareReleaseTags), ascending);
  for (const [a, b] of corpus.equivalent) assert.equal(compareReleaseTags(`v${a}`, `v${b}`), 0);
  assert.equal(compareReleaseTags("v1.5.0-rc.2", "v1.5.0-rc.10"), -1);
  assert.equal(compareReleaseTags("v1.5.0.9000", "v1.5.0.9001"), -1);
  assert.equal(parseReleaseTag("v1.5.0.9000").legacy, true);
});

test("legacy docs guards parse all reader identities but reject controller ownership", () => {
  assert.equal(legacyDocsBranch("v1.0.0"), "main");
  assert.equal(legacyDocsBranch("v1.0.0.9000"), "dev");
  assert.throws(() => legacyDocsBranch("v1.1.0-rc.10"), /controller/i);
  assert.throws(() => legacyDocsBranch("v1.0.0+build-x"), /controller/i);
  assert.throws(() => legacyDocsBranch("v1.0.0", {tag: "v1.0.0"}), /controller/i);
  assert.throws(() => legacyDocsBranch("v01.0.0"), /tag/i);
});

test("stable source policy accepts configured deployment branches and remote default", () => {
  const policy = {production_branches: ["deploy/1.x"]};
  assert.equal(assertReleaseSource("v1.2.3", "production", "production", policy), "production");
  assert.equal(assertReleaseSource("v1.2.3", "deploy/1.x", "production", policy), "deploy/1.x");
  assert.throws(() => assertReleaseSource("v1.2.3", "feature/test", "production", policy), /Stable release source branch/);
  assert.throws(() => assertReleaseSource("v1.2.3", "dev", "production", policy), /Stable release source branch/);
});

test("four-component source policy accepts any valid same-repository candidate branch", () => {
  for (const branch of ["feature/test", "dev", "production", "deploy/1.x"]) {
    assert.equal(assertReleaseSource("v1.2.3.4", branch, "production", {production_branches: []}), branch);
  }
});

test("source policy rejects malformed branch authority instead of treating it as permission", () => {
  for (const production_branches of [null, "feature/test", [null], ["../bad"], ["--all"], ["bad name"]]) {
    assert.throws(() => assertReleaseSource("v1.2.3", "feature/test", "production", {production_branches}), /production_branches/);
  }
  for (const branch of ["../bad", "--all", "bad name", "feature..bad", "feature@{1}", "feature\\bad", "feature.lock", "feature/", ""]) {
    assert.throws(() => assertReleaseSource("v1.2.3.4", branch, "production", {production_branches: []}), /branch/i);
  }
});

test("missing legacy production policy permits only the remote default for stable releases", () => {
  assert.equal(assertReleaseSource("v1.2.3", "production", "production", null), "production");
  assert.throws(() => assertReleaseSource("v1.2.3", "main", "production", null), /Stable release source branch/);
  assert.equal(assertReleaseSource("v1.2.3.4", "feature/test", "production", null), "feature/test");
});

test("source policy does not take over controller-owned release identities", () => {
  for (const tag of ["v1.2.3-rc.1", "v1.2.3+build.1"]) {
    assert.throws(() => assertReleaseSource(tag, "production", "production", null), /Controller-owned release/);
  }
});

function sourceFixture(tag = "v1.2.3.4", branch = "feature/test") {
  const sha = "a".repeat(40), controller = "b".repeat(40), tip = "c".repeat(40);
  const env = {GITHUB_REPOSITORY: "owner/repo", GITHUB_REPOSITORY_ID: "123", RELEASE_TAG: tag, RELEASE_SHA: sha};
  const state = {calls: [], repo: {id: 123, full_name: "owner/repo", fork: false, default_branch: "production"},
    policy: {enabled: false, production_branches: ["deploy/1.x"]}, rawPolicy: null,
    latestByCommit: {},
    branches: [branch], source: branch, protected: true, status: "ahead", absent: false, changed: false, defaultChanged: false};
  let comparisons = 0;
  const transport = (exe, args) => {
    assert.equal(exe, "gh");
    assert.equal(args[args.indexOf("--method") + 1], "GET");
    const endpoint = args.at(-1).replace("repos/owner/repo", "");
    state.calls.push(endpoint);
    let value;
    if (!endpoint) value = state.repo;
    else if (endpoint === "/branches/production") value = {name: "production", protected: state.protected,
      commit: {sha: comparisons && state.defaultChanged ? "e".repeat(40) : controller}};
    else if (endpoint === `/contents/.release-controller.json?ref=${controller}`) {
      value = {type: "file", encoding: "base64", content: Buffer.from(state.rawPolicy ?? JSON.stringify(state.policy)).toString("base64")};
    } else if (endpoint.startsWith('/contents/releases/')) {
      const commit = endpoint.split('?ref=')[1];
      const raw = endpoint.startsWith('/contents/releases/latest.json') ?
        (state.latestByCommit[commit] ?? JSON.stringify({tag})) : JSON.stringify({tag});
      if (raw === 'missing') return 'HTTP/2.0 404 Not Found\n\n{}';
      value = {type: 'file', encoding: 'base64', content: Buffer.from(raw).toString('base64')};
    } else if (endpoint.startsWith("/branches?")) value = state.branches.map(name => ({name}));
    else if (endpoint === `/branches/${encodeURIComponent(state.source)}`) {
      if (state.absent) return 'HTTP/2.0 404 Not Found\n\n{}';
      value = {name: state.source, commit: {sha: comparisons && state.changed ? "d".repeat(40) : tip}};
    } else if (endpoint.startsWith(`/compare/${sha}...`)) {
      comparisons++;
      value = {base_commit: {sha}, merge_base_commit: {sha: state.status === "diverged" ? "d".repeat(40) : sha}, status: state.status};
    } else throw Error("Unexpected source-policy I/O: " + endpoint);
    return "HTTP/2.0 200 OK\n\n" + JSON.stringify(value);
  };
  return {env, state, transport};
}

test("tag build resolves a prerelease feature branch with remote policy and exact SHA evidence", () => {
  const f = sourceFixture();
  assert.equal(resolveReleaseSource(f.env, f.transport), "feature/test");
  assert.ok(f.state.calls.includes("/branches/feature%2Ftest"));
  assert.ok(f.state.calls.includes(`/contents/.release-controller.json?ref=${"b".repeat(40)}`));
  assert.ok(f.state.calls.includes(`/compare/${"a".repeat(40)}...${"c".repeat(40)}`));
});

test("stable docs accepts either the remote default or an explicitly configured deployment source", () => {
  for (const branch of ["production", "deploy/1.x"]) {
    const f = sourceFixture("v1.2.3", branch);
    f.env.RELEASE_SOURCE_BRANCH = branch;
    assert.equal(resolveReleaseSource(f.env, f.transport), branch);
  }
  const f = sourceFixture("v1.2.3");
  f.env.RELEASE_SOURCE_BRANCH = "feature/test";
  assert.throws(() => resolveReleaseSource(f.env, f.transport), /Stable release source branch/);
  assert.ok(!f.state.calls.some(call => call.includes("/compare/")));
});

test("source resolution rejects unavailable, unrelated, moved or unauthorized remote evidence", () => {
  for (const mutate of [f => {f.state.absent = true;}, f => {f.state.status = "diverged";},
    f => {f.state.changed = true;}, f => {f.state.defaultChanged = true;}, f => {f.state.protected = false;},
    f => {f.state.repo.fork = true;}, f => {f.state.repo.id++;}, f => {f.state.repo.full_name = "other/repo";}]) {
    const f = sourceFixture(); mutate(f);
    assert.throws(() => resolveReleaseSource(f.env, f.transport));
  }
});

test("automatic stable source skips containing default with newer prerelease payload", () => {
  const f = sourceFixture('v1.2.3', 'deploy/1.x');
  f.state.latestByCommit['b'.repeat(40)] = JSON.stringify({tag: 'v1.2.4.9000'});
  assert.equal(resolveReleaseSource(f.env, f.transport), 'deploy/1.x');
  assert.ok(f.state.calls.includes('/branches/production'));
  assert.ok(f.state.calls.includes('/branches/deploy%2F1.x'));
  f.env.RELEASE_SOURCE_BRANCH = 'production';
  assert.throws(() => resolveReleaseSource(f.env, f.transport), /current payload/);
});

test("source resolution rejects tagged payload skew and absence of any current matching source", () => {
  const f = sourceFixture();
  f.state.latestByCommit['a'.repeat(40)] = JSON.stringify({tag: 'v1.2.4.9000'});
  assert.throws(() => resolveReleaseSource(f.env, f.transport), /tagged latest bytes/);
  delete f.state.latestByCommit['a'.repeat(40)];
  f.state.latestByCommit['c'.repeat(40)] = 'missing';
  assert.throws(() => resolveReleaseSource(f.env, f.transport), /current payload/);
});

test("source resolution fails closed for malformed and duplicate protected policy", () => {
  for (const raw of ['{"enabled":false,"production_branches":"feature/test"}',
    '{"enabled":false,"production_branches":[null]}',
    '{"enabled":false,"production_branches":[],"production_branches":["feature/test"]}',
    '{"enabled":false,"enabled":true}', '{"enabled":true,"production_branches":[]}']) {
    const f = sourceFixture(); f.state.rawPolicy = raw;
    assert.throws(() => resolveReleaseSource(f.env, f.transport));
  }
});

test("source inventory is bounded and explicit candidates avoid branch enumeration", () => {
  const f = sourceFixture();
  f.state.branches = Array.from({length: 100}, (_, i) => `feature/test-${i}`);
  assert.throws(() => resolveReleaseSource(f.env, f.transport), /inventory exceeds bound/);
  assert.equal(f.state.calls.filter(call => call.startsWith("/branches?")).length, 20);
  f.state.calls.length = 0;
  f.env.RELEASE_SOURCE_BRANCH = "feature/test";
  assert.equal(resolveReleaseSource(f.env, f.transport), "feature/test");
  assert.ok(!f.state.calls.some(call => call.startsWith("/branches?")));
});

test("full-site tag CLI excludes prereleases but does not map source branches", () => {
  const {spawnSync} = require("node:child_process");
  const script = path.resolve(__dirname, "../release-version.js");
  for (const [tag, expected] of [["v1.2.3", "true"], ["v1.2.3.4", "false"]]) {
    const result = spawnSync(process.execPath, [script, "--full-site-tag", tag], {encoding: "utf8", timeout: 10000});
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.trim(), expected);
  }
});

test("complete payload loader accepts SemVer filenames and preserves exact latest bytes", t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "cg-payload-reader-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.mkdirSync(path.join(root, "releases"));
  const tag = "v1.5.0-rc.10+build.2";
  const payload = { schemaVersion: 1, tag, publishedAt: "2026-09-12T00:00:00Z", releaseDate: "2026-09-12",
    name: tag, url: `https://github.com/GPID-WB/compound-gpid/releases/tag/${tag}`, sourceUrl: `https://github.com/GPID-WB/compound-gpid/tree/${tag}`,
    sections: [{kind: "internal", title: "Reviewed changes", entries: ["Exact bytes"]}] };
  const raw = JSON.stringify(payload) + "\n";
  fs.writeFileSync(path.join(root, "releases", tag + ".json"), raw);
  fs.writeFileSync(path.join(root, "releases/latest.json"), raw);
  assert.deepEqual(loadReleasePayloads(root)[0].raw, Buffer.from(raw));
  fs.appendFileSync(path.join(root, "releases/latest.json"), "\n");
  const result = require("node:child_process").spawnSync(process.execPath,
    [path.resolve(__dirname, "../generate-whats-new.js"), "--root", root, "--validate-release-set"], {encoding: "utf8"});
  assert.equal(result.status, 1);
  assert.match(result.stderr, /byte-match/);
});
