"use strict";

// Durable official bytes travel with the existing Pages deployment. There is no
// state branch, Release asset write, or second publisher in this protocol.
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const crypto = require('node:crypto'), {execFileSync} = require('node:child_process');
const {check, githubGet} = require('./legacy-pages.js');
const {buildSnapshot, exportSnapshot, inventory} = require('./docs-snapshots.js');
const {strictJson, validateEnvelope, MAX_ENVELOPE} = require('./snapshot-data.js');
const {parseReleaseTag, resolveReleaseSource} = require('./release-version.js');
const FILE = 'cg-official-snapshot.json';
const LIMIT = MAX_ENVELOPE + 4096;
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const positive = value => Number.isSafeInteger(value) && value > 0;
function fail(message) { throw Error('official-snapshot: ' + message); }

function publisher(env) {
  const result = {runId: Number(env.GITHUB_RUN_ID), runAttempt: Number(env.GITHUB_RUN_ATTEMPT),
    sha: env.GITHUB_SHA, branch: env.GITHUB_REF_NAME, job: env.GITHUB_JOB};
  if (!positive(result.runId) || !positive(result.runAttempt) || !/^[0-9a-f]{40}$/.test(result.sha) ||
      typeof result.branch !== 'string' || /[\r\n]/.test(result.branch) || !['deploy', 'deploy-dev'].includes(result.job)) fail('invalid publisher identity');
  return result;
}

function validate(value, repoId) {
  if (!value || Object.keys(value).sort().join() !== 'official,officialBranch,publisher,repositoryId,schemaVersion' ||
      value.schemaVersion !== 1 || value.repositoryId !== repoId || typeof value.officialBranch !== 'string' ||
      !value.officialBranch || value.officialBranch.length > 1024 || /[\r\n]/.test(value.officialBranch)) fail('invalid durable official identity');
  validateEnvelope(value.official, {kind: 'release'});
  const tag = parseReleaseTag(value.official.record.tag);
  if (tag.legacy || tag.prerelease.length || value.official.record.tag.includes('+') || Object.hasOwn(value.official.files, FILE)) fail('official snapshot must contain only stable release bytes');
  const p = value.publisher;
  if (!p || Object.keys(p).sort().join() !== 'branch,job,runAttempt,runId,sha') fail('invalid durable publisher');
  publisher({GITHUB_RUN_ID: p.runId, GITHUB_RUN_ATTEMPT: p.runAttempt, GITHUB_SHA: p.sha, GITHUB_REF_NAME: p.branch, GITHUB_JOB: p.job});
  return value;
}

/** Verify the current served snapshot through a durable Pages deployment, not old build runs.
 * Example: readOfficial(process.env). No credentials are sent to the public site.
 */
function readOfficial(env, transport = execFileSync) {
  check(env, transport);
  const base = `repos/${env.GITHUB_REPOSITORY}`, get = endpoint => githubGet(endpoint, transport);
  const repo = get(base), pages = get(`${base}/pages`);
  const [owner, repository] = env.GITHUB_REPOSITORY.split('/');
  const expected = `https://${owner.toLowerCase()}.github.io/${repository}/`;
  if (repo.id !== Number(env.GITHUB_REPOSITORY_ID) || repo.full_name !== env.GITHUB_REPOSITORY || repo.fork !== false ||
      pages.build_type !== 'workflow' || pages.html_url !== expected || pages.cname) fail('Pages must be this repository\'s workflow-managed HTTPS origin');
  // A unique query prevents a cached previous site from being mistaken for the
  // latest deployment; the deployment identity below also rejects stale bytes.
  const url = `${expected}${FILE}?verify=${crypto.randomUUID()}`;
  const raw = transport('curl', ['--disable', '--fail', '--silent', '--show-error', '--proto', '=https',
    '--tlsv1.2', '--max-time', '60', '--max-filesize', String(LIMIT), '--max-redirs', '0',
    '--header', 'Cache-Control: no-cache', url], {timeout: 65000, maxBuffer: LIMIT, stdio: ['ignore', 'pipe', 'pipe']});
  if (!raw || raw.length > LIMIT) fail('durable official response exceeds bound');
  const bytes = Buffer.from(raw), value = validate(strictJson(bytes), repo.id), p = value.publisher;
  let current;
  // This follows the CURRENT environment pointer. Hundreds of dev previews do
  // not require finding the old official workflow in mixed Actions history.
  for (let page = 1; !current; page++) {
    if (page > 100) fail('excessive unsuccessful Pages deployment history');
    const deployments = get(`${base}/deployments?environment=github-pages&per_page=100&page=${page}`);
    if (!Array.isArray(deployments) || deployments.length > 100) fail('invalid Pages deployment inventory');
    for (const deployment of deployments) {
      if (!positive(deployment.id) || deployment.environment !== 'github-pages') fail('invalid Pages deployment identity');
      const statuses = get(`${base}/deployments/${deployment.id}/statuses?per_page=100`);
      if (!Array.isArray(statuses) || statuses.length > 100) fail('invalid Pages deployment statuses');
      // GitHub marks previous successful deployments inactive after a successor.
      const status = statuses[0];
      if (status?.state === 'success') { current = {deployment, status}; break; }
    }
    if (!current && deployments.length < 100) fail('no current successful Pages deployment');
  }
  const {deployment, status} = current;
  const prefix = `https://github.com/${env.GITHUB_REPOSITORY}/actions/runs/${p.runId}/job/`;
  if (deployment.sha !== p.sha || deployment.ref !== repo.default_branch || p.branch !== repo.default_branch ||
      !status.log_url?.startsWith(prefix) || !/^[1-9][0-9]*$/.test(status.log_url.slice(prefix.length))) fail('served snapshot is not the current protected Pages deployment');
  const job = get(`${base}/actions/jobs/${status.log_url.slice(prefix.length)}`);
  const run = get(`${base}/actions/runs/${p.runId}/attempts/${p.runAttempt}`);
  const step = p.job === 'deploy' ? 'Deploy to GitHub Pages' : 'Deploy development preview to GitHub Pages';
  if (job.id !== Number(status.log_url.slice(prefix.length)) || job.run_id !== p.runId || job.run_attempt !== p.runAttempt || job.name !== p.job || job.head_sha !== p.sha ||
      job.status !== 'completed' || job.conclusion !== 'success' ||
      job.steps?.filter(s => s.name === step && s.conclusion === 'success').length !== 1 ||
      run.id !== p.runId || run.run_attempt !== p.runAttempt || run.repository?.id !== repo.id ||
      run.path !== '.github/workflows/release-pages.yml' || !['workflow_run', 'workflow_dispatch'].includes(run.event) || run.head_sha !== p.sha || run.head_branch !== p.branch ||
      run.status !== 'completed' || run.conclusion !== 'success') fail('current Pages publisher is not the protected controller');
  const ancestry = get(`${base}/compare/${p.sha}...${env.GITHUB_SHA}`);
  if (ancestry.base_commit?.sha !== p.sha || ancestry.merge_base_commit?.sha !== p.sha ||
      !['ahead', 'identical'].includes(ancestry.status)) fail('Pages publisher is outside protected controller lineage');
  check(env, transport);
  return {value, bytes};
}

// Add the state to the same atomic Pages artifact; only a successful deployment
// makes a new official snapshot visible. Previews replace only the publisher tuple.
function stamp(value, artifact, env) {
  value = validate({...value, publisher: publisher(env)}, Number(env.GITHUB_REPOSITORY_ID));
  const site = path.join(artifact, 'site'), files = inventory(site);
  for (const [name, digest] of Object.entries(value.official.record.files)) if (files[name] !== digest) fail('composition changed official bytes');
  if (Object.keys(files).some(name => !name.startsWith('dev/') && !Object.hasOwn(value.official.record.files, name))) fail('unexpected official composition path');
  const raw = Buffer.from(JSON.stringify(value) + '\n');
  if (raw.length > LIMIT) fail('durable snapshot capacity exceeded');
  const metadataPath = path.join(artifact, '.docs-build-metadata.json');
  const metadata = strictJson(fs.readFileSync(metadataPath));
  if (metadata.schemaVersion !== 1 || !metadata.site?.files ||
      JSON.stringify(Object.keys(metadata.site.files).sort()) !== JSON.stringify(Object.keys(files).sort()) ||
      Object.keys(files).some(name => metadata.site.files[name] !== files[name])) fail('composition inventory differs before snapshot stamp');
  fs.writeFileSync(path.join(site, FILE), raw, {flag: 'wx'});
  metadata.site.files[FILE] = hash(raw);
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2) + '\n');
}

/** Seal verified stable docs into the existing deployment artifact. Example: sealOfficial(env, source, artifact). */
function sealOfficial(env, source, artifact, transport = execFileSync) {
  if (env.GITHUB_JOB !== 'deploy') fail('only official deployment may replace official snapshot');
  const authority = check(env, transport);
  const branch = resolveReleaseSource({...env, RELEASE_TAG: authority.release_tag, RELEASE_SHA: authority.release_sha,
    RELEASE_SOURCE_BRANCH: env.RELEASE_BRANCH}, transport);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'cg-official-'));
  try {
    const snapshot = path.join(temp, 'snapshot'), envelope = path.join(temp, 'snapshot.json');
    buildSnapshot({root: source, out: snapshot, kind: 'release', tag: authority.release_tag, sha: authority.release_sha,
      runId: authority.build_run_id, runAttempt: 1});
    exportSnapshot(snapshot, envelope);
    stamp({schemaVersion: 1, repositoryId: Number(env.GITHUB_REPOSITORY_ID), officialBranch: branch,
      official: strictJson(fs.readFileSync(envelope))}, artifact, env);
  } finally { fs.rmSync(temp, {recursive: true, force: true}); }
}

/** Restore only verified immutable official bytes, independent of current source branches/artifacts. */
function restoreOfficial(env, source, stateFile, transport = execFileSync) {
  const {value, bytes} = readOfficial(env, transport);
  fs.mkdirSync(source);
  fs.mkdirSync(path.join(source, 'docs'));
  for (const [name, encoded] of Object.entries(value.official.files)) {
    const target = path.join(source, 'docs', name);
    fs.mkdirSync(path.dirname(target), {recursive: true});
    fs.writeFileSync(target, Buffer.from(encoded, 'base64'), {flag: 'wx'});
  }
  fs.writeFileSync(stateFile, bytes, {flag: 'wx'});
  return {official_tag: value.official.record.tag, official_sha: value.official.record.sha, official_branch: value.officialBranch};
}

/** Stamp a preview with the unchanged official envelope; recheck just before deployment separately. */
function stampPreview(env, stateFile, artifact) {
  if (env.GITHUB_JOB !== 'deploy-dev') fail('only preview may carry an existing official snapshot');
  stamp(strictJson(fs.readFileSync(stateFile)), artifact, env);
}

/** Reject a concurrent/stale snapshot before preview publication. */
function recheckOfficial(env, stateFile, transport = execFileSync) {
  if (!readOfficial(env, transport).bytes.equals(fs.readFileSync(stateFile))) fail('official state changed before preview deployment');
}

module.exports = {readOfficial, sealOfficial, restoreOfficial, stampPreview, recheckOfficial, FILE};
