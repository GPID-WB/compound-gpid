"use strict";
// Trusted legacy Pages gate. Only the protected default workflow may execute it.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');

function fail(message) { throw Error('legacy-pages: ' + message); }
function positive(value) { return Number.isSafeInteger(value) && value > 0; }

// Bounded GET only. Reused by authority and official deployment snapshot reads.
function githubGet(endpoint, transport, optional = false) {
  let raw, failed = false;
  try {
    raw = transport('gh', ['api', '--method', 'GET', '--hostname', 'github.com', '--include', endpoint],
      {encoding: 'utf8', timeout: 20000, maxBuffer: 4194304, stdio: ['ignore', 'pipe', 'pipe']});
  } catch (error) { failed = true; raw = error.stdout; }
  if (!raw || raw.length > 4194304) fail('bounded remote authority read failed');
  const text = raw.toString().replace(/\r\n/g, '\n'), split = text.indexOf('\n\n');
  const status = text.match(/^HTTP\/[\d.]+ (\d{3})\b/);
  if (split < 0 || !status) fail('unverifiable HTTP response');
  if (optional && status[1] === '404') return null;
  if (failed || status[1] !== '200') fail('remote authority read failed');
  return JSON.parse(text.slice(split + 2));
}

// Example: check(process.env). All remote calls are GETs; transport is outer I/O only.
function check(env, transport = execFileSync) {
  const slug = env.GITHUB_REPOSITORY;
  const repoId = Number(env.GITHUB_REPOSITORY_ID);
  const runId = Number(env.BUILD_RUN_ID);
  const actorId = Number(env.GITHUB_ACTOR_ID);
  const mode = env.LEGACY_MODE;
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(slug) ||
      !positive(repoId) || !positive(runId) || !positive(actorId) ||
      !['dev', 'release', 'recovery'].includes(mode)) fail('invalid request identity');
  const base = `repos/${slug}`;
  const get = (endpoint, optional = false) => githubGet(endpoint, transport, optional);
  function document(file, sha) {
    const value = get(`${base}/contents/${file}?ref=${sha}`, true);
    if (value === null) return null;
    if (value.type !== 'file' || value.encoding !== 'base64' || typeof value.content !== 'string') fail('invalid authority document');
    const raw = Buffer.from(value.content, 'base64').toString('utf8');
    const keys = [...raw.matchAll(/("(?:\\.|[^"\\])*")\s*:/g)].map(m => JSON.parse(m[1]));
    if (file === '.release-controller.json' ? keys.filter(k => k === 'enabled').length !== 1 : new Set(keys).size !== keys.length) fail('ambiguous authority document');
    return JSON.parse(raw);
  }
  function authority(id, historical = false) {
    if (!positive(id)) fail('missing current actor authority');
    const user = get(`user/${id}`);
    if (user.id !== id || !/^[A-Za-z0-9-]+$/.test(user.login)) fail('invalid actor authority');
    const role = get(`${base}/collaborators/${user.login}/permission`);
    if (role.user?.id !== id || !(historical ? ['maintain', 'admin'] : ['write', 'maintain', 'admin']).includes(role.role_name) ||
      role.permission !== (role.role_name === 'admin' ? 'admin' : 'write')) fail('current actor authority revoked');
  }
  const repo = get(base);
  if (repo.id !== repoId || repo.fork !== false || typeof repo.default_branch !== 'string') fail('repository identity differs');
  const branchPath = `${base}/branches/${encodeURIComponent(repo.default_branch)}`;
  const branch = get(branchPath);
  if (branch.name !== repo.default_branch || branch.protected !== true ||
      !/^[0-9a-f]{40}$/.test(branch.commit?.sha) || branch.commit.sha !== env.GITHUB_SHA) fail('protected default policy changed');
  // Normal Pages tokens can read the protected branch and exact policy bytes,
  // but not administration metadata. A reviewed recovery record needs the App.
  if (mode === 'recovery') {
    const protection = get(branchPath + '/protection');
    const review = protection.required_pull_request_reviews;
    if (protection.enforce_admins?.enabled !== true || protection.allow_force_pushes?.enabled !== false ||
        protection.allow_deletions?.enabled !== false || !positive(review?.required_approving_review_count) ||
        review.dismiss_stale_reviews !== true || !review.bypass_pull_request_allowances ||
        Object.values(review.bypass_pull_request_allowances).some(a => !Array.isArray(a) || a.length)) fail('protected default review controls missing');
  }
  const policy = document('.release-controller.json', branch.commit.sha);
  if (policy !== null && (typeof policy.enabled !== 'boolean' || (policy.enabled && mode !== 'recovery'))) fail('legacy deployment disabled after cutover');
  const run = get(`${base}/actions/runs/${runId}`);
  if (run.id !== runId || run.run_attempt !== 1 || run.repository?.id !== repoId ||
      run.status !== 'completed' || run.conclusion !== 'success' || !/^[0-9a-f]{40}$/.test(run.head_sha) ||
      run.path !== (mode === 'dev' ? '.github/workflows/pages.yml' : '.github/workflows/release-docs.yml') ||
      !(mode === 'dev' ? ['push', 'workflow_dispatch'] : ['push']).includes(run.event) ||
      (mode === 'dev' && run.head_branch !== 'dev')) fail('exact successful source run is required');
  authority(actorId, mode === 'recovery');
  // A current reviewed recovery grant replaces historical build actors, not tag identity.
  if (mode !== 'recovery') {
    authority(run.actor?.id);
    authority(run.triggering_actor?.id);
  }
  const inventory = get(`${base}/actions/runs/${runId}/artifacts?per_page=100&page=1`);
  if (!Array.isArray(inventory.artifacts) || inventory.artifacts.length !== inventory.total_count || inventory.total_count > 100) fail('incomplete artifact inventory');
  const artifacts = inventory.artifacts.filter(a => a.name === (mode === 'dev' ? 'legacy-dev-docs' : 'release-docs-site'));
  const artifact = artifacts[0];
  if (artifacts.length !== 1 || !positive(artifact.id) || artifact.expired !== false ||
      artifact.workflow_run?.id !== runId || artifact.workflow_run.head_sha !== run.head_sha ||
      !/^sha256:[0-9a-f]{64}$/.test(artifact.digest)) fail('exact artifact identity is invalid');
  if (mode !== 'dev') {
    const versions = require('./release-version.js');
    versions.legacyDocsBranch(run.head_branch);
    if (versions.parseReleaseTag(run.head_branch).legacy) fail('prerelease full-site deployment is disabled');
  }
  if (mode === 'recovery') {
    const record = document(`.github/release-recovery/${run.head_branch}.json`, branch.commit.sha);
    const ref = get(`${base}/git/ref/tags/${encodeURIComponent(run.head_branch)}`);
    if (ref.ref !== 'refs/tags/' + run.head_branch || ref.object?.type !== 'tag' || !/^[0-9a-f]{40}$/.test(ref.object.sha)) fail('historical immutable tag is required');
    const tag = get(`${base}/git/tags/${ref.object.sha}`);
    if (!record || record.schema_version !== 1 || record.repository_id !== repoId ||
        record.tag !== run.head_branch || record.tag_object !== ref.object.sha ||
        tag.sha !== ref.object.sha || tag.tag !== run.head_branch || tag.object?.type !== 'commit' ||
        tag.object.sha !== run.head_sha || record.release_sha !== run.head_sha ||
        record.build_run_id !== runId || record.artifact_id !== artifact.id || record.artifact_digest !== artifact.digest ||
        !Array.isArray(record.actor_ids) || !record.actor_ids.every(positive) || !record.actor_ids.includes(actorId) ||
        typeof record.reason !== 'string' || !record.reason.trim()) fail('reviewed historical tag/artifact authority differs');
  }
  if (get(base).default_branch !== repo.default_branch || get(branchPath).commit.sha !== branch.commit.sha) fail('protected default policy advanced');
  const result = {artifact_id: artifact.id, artifact_digest: artifact.digest, build_run_id: runId,
    release_tag: run.head_branch, release_sha: run.head_sha, policy_sha: branch.commit.sha};
  const dev = inventory.artifacts.filter(a => a.name === 'release-dev-docs');
  if (mode !== 'dev' && dev.length) {
    if (dev.length !== 1 || !positive(dev[0].id) || dev[0].expired !== false ||
        dev[0].workflow_run?.id !== runId || dev[0].workflow_run.head_sha !== run.head_sha ||
        !/^sha256:[0-9a-f]{64}$/.test(dev[0].digest)) fail('invalid isolated dev artifact');
    result.dev_artifact_id = dev[0].id;
    result.dev_artifact_digest = dev[0].digest;
  }
  return result;
}

// Fail before extraction if the exact GitHub archive differs from its recorded digest.
function verifyArchive(env, id, expected, transport = execFileSync) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(env.GITHUB_REPOSITORY) ||
      !positive(Number(id)) || !/^sha256:[0-9a-f]{64}$/.test(expected)) fail('invalid artifact binding');
  const raw = transport('gh', ['api', '--method', 'GET', '--hostname', 'github.com', `repos/${env.GITHUB_REPOSITORY}/actions/artifacts/${id}/zip`],
    {timeout: 20000, maxBuffer: 134217728});
  if ('sha256:' + crypto.createHash('sha256').update(raw).digest('hex') !== expected) fail('artifact archive digest mismatch');
}

// Import only verified dev docs as data. Stable files and trusted scripts stay untouched.
function importDev(source, artifact, staging) {
  return require('./docs-provenance.js').importVerified(source, artifact, staging);
}

module.exports = {check, verifyArchive, importDev, githubGet};

if (require.main === module) {
  try {
    if (['check', 'restore-official'].includes(process.argv[2])) {
      const result = process.argv[2] === 'check' ? check(process.env) :
        require('./legacy-official-snapshot.js').restoreOfficial(process.env, process.argv[3], process.argv[4]);
      if (process.env.GITHUB_OUTPUT) fs.appendFileSync(process.env.GITHUB_OUTPUT,
        Object.entries(result).map(([k, v]) => `${k}=${v}\n`).join(''));
    } else if (process.argv[2] === 'archive') verifyArchive(process.env, process.argv[3], process.argv[4]);
else if (['import-dev', 'import-docs'].includes(process.argv[2])) importDev(process.argv[3], process.argv[4], process.argv[5]);
    else if (process.argv[2] === 'seal-official') require('./legacy-official-snapshot.js').sealOfficial(process.env, process.argv[3], process.argv[4]);
    else if (process.argv[2] === 'stamp-preview') require('./legacy-official-snapshot.js').stampPreview(process.env, process.argv[3], process.argv[4]);
    else if (process.argv[2] === 'recheck-official') require('./legacy-official-snapshot.js').recheckOfficial(process.env, process.argv[3]);
    else fail('unknown operation');
  } catch (error) {
    console.error(/^(legacy-pages|official-snapshot):/.test(error.message) ? error.message : 'legacy-pages: bounded verification failed');
    process.exitCode = 1;
  }
}
