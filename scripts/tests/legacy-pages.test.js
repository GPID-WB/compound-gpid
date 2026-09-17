"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const { check, verifyArchive, importDev } = require('../legacy-pages.js');

test('production stable validation argv reaches the real validator interface', () => {
  const fs = require('node:fs'), path = require('node:path');
  const {spawnSync} = require('node:child_process');
  const root = path.resolve(__dirname, '../..');
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/release-pages.yml'), 'utf8');
  const command = workflow.match(/node scripts\/check-docs-site\.js ([^\n]+)/)[1];
  const args = command.trim().split(/\s+/).map(value => value === 'sources/main' ? root : value);
  const result = spawnSync(process.execPath, [path.join(root, 'scripts/check-docs-site.js'), ...args], {encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr + result.stdout);
});

function fixture() {
  const sha = 'a'.repeat(40);
  const state = { enabled: false, protected: true, role: 'write', calls: [], recovery: null };
  const env = { GITHUB_REPOSITORY: 'owner/repo', GITHUB_REPOSITORY_ID: '123',
    GITHUB_SHA: sha, GITHUB_ACTOR_ID: '8', BUILD_RUN_ID: '10', LEGACY_MODE: 'dev' };
  const run = { id: 10, run_attempt: 1, event: 'push', path: '.github/workflows/pages.yml',
    head_sha: 'b'.repeat(40), head_branch: 'dev', repository: {id: 123},
    status: 'completed', conclusion: 'success', actor: {id: 7}, triggering_actor: {id: 7} };
  const artifact = { id: 20, name: 'legacy-dev-docs', expired: false, digest: 'sha256:' + 'c'.repeat(64),
    workflow_run: {id: 10, head_sha: run.head_sha} };
  const transport = (exe, args) => {
    assert.equal(exe, 'gh');
    assert.ok(args.includes('GET'));
    const endpoint = args.at(-1).replace('repos/owner/repo', '');
    state.calls.push(endpoint);
    let value;
    if (!endpoint) value = {id: 123, default_branch: 'production', fork: false};
    else if (endpoint === '/branches/production') value = {name: 'production', protected: state.protected, commit: {sha}};
    else if (endpoint === '/branches/production/protection') {
      if (state.denyAdministration) throw Object.assign(Error('administration unavailable'), {stdout: 'HTTP/2.0 403 Forbidden\n\n{}'});
      value = {enforce_admins: {enabled: true}, allow_force_pushes: {enabled: false}, allow_deletions: {enabled: false}, required_pull_request_reviews: {required_approving_review_count: 1, dismiss_stale_reviews: true, bypass_pull_request_allowances: {users: [], teams: [], apps: []}}};
    }
    else if (endpoint === '/contents/.release-controller.json?ref=' + sha) value = {type: 'file', encoding: 'base64', content: Buffer.from(JSON.stringify({enabled: state.enabled})).toString('base64')};
    else if (endpoint === '/actions/runs/10') value = run;
    else if (endpoint === '/actions/runs/10/artifacts?per_page=100&page=1') value = {total_count: 1, artifacts: [artifact]};
    else if (/^user\/[78]$/.test(endpoint)) value = {id: Number(endpoint.split('/')[1]), login: 'actor' + endpoint.split('/')[1]};
    else if (/^\/collaborators\/actor[78]\/permission$/.test(endpoint)) {
      const id = Number(endpoint.match(/actor([78])/)[1]);
      const role = state.roles?.[id] || state.role;
      value = {user: {id}, role_name: role, permission: role === 'maintain' ? 'write' : role};
    }
    else if (endpoint.startsWith('/contents/.github/release-recovery/')) value = state.recovery;
    else if (endpoint.startsWith('/git/ref/tags/')) value = {ref: 'refs/tags/' + run.head_branch, object: {type: 'tag', sha: 'e'.repeat(40)}};
    else if (endpoint === '/git/tags/' + 'e'.repeat(40)) value = {tag: run.head_branch, sha: 'e'.repeat(40), object: {type: 'commit', sha: run.head_sha}};
    else throw Error('Unexpected outer I/O: ' + endpoint);
    return 'HTTP/2.0 200 OK\n\n' + JSON.stringify(value);
  };
  return {state, env, run, artifact, transport};
}

test('protected remote default other than main selects cutover authority', () => {
  const f = fixture();
  assert.equal(check(f.env, f.transport).artifact_id, 20);
  assert.ok(f.state.calls.includes('/contents/.release-controller.json?ref=' + f.env.GITHUB_SHA));
  f.state.enabled = true;
  assert.throws(() => check(f.env, f.transport), /cutover/);
});
test('routine legacy gate uses metadata permissions while reviewed recovery requires administration', () => {
  const f = fixture();
  f.state.denyAdministration = true;
  assert.equal(check(f.env, f.transport).artifact_id, 20);
  assert.ok(!f.state.calls.some(endpoint => endpoint.endsWith('/protection')));
  f.env.LEGACY_MODE = 'recovery';
  assert.throws(() => check(f.env, f.transport), /authority read failed/);
});
test('delayed queue rechecks default protection and original actor revocation', () => {
  const f = fixture();
  check(f.env, f.transport);
  f.state.roles = {7: 'read'};
  assert.throws(() => check(f.env, f.transport), /authority/);
  f.state.roles = {}; f.state.protected = false;
  assert.throws(() => check(f.env, f.transport), /protected/);
});
test('exact successful source run and full artifact identity are mandatory', () => {
  for (const mutate of [f => f.run.repository.id++, f => f.run.run_attempt++,
    f => f.artifact.workflow_run.id++, f => f.artifact.expired = true,
    f => f.run.conclusion = 'failure']) {
    const f = fixture(); mutate(f);
    assert.throws(() => check(f.env, f.transport));
  }
});
test('post-cutover recovery requires a reviewed exact immutable tag and artifact record', () => {
  const f = fixture();
  f.env.LEGACY_MODE = 'recovery'; f.state.enabled = true; f.state.role = 'maintain';
  f.run.path = '.github/workflows/release-docs.yml'; f.run.head_branch = 'v1.2.0.9015';
  f.artifact.name = 'release-docs-site';
  assert.throws(() => check(f.env, f.transport), /historical/);
  const record = {schema_version: 1, repository_id: 123, tag: f.run.head_branch,
    tag_object: 'e'.repeat(40), release_sha: f.run.head_sha, actor_ids: [7, 8],
    reason: 'Recover failed deployment', build_run_id: 10, artifact_id: 20,
    artifact_digest: f.artifact.digest};
  f.state.recovery = {type: 'file', encoding: 'base64', content: Buffer.from(JSON.stringify(record)).toString('base64')};
  f.state.roles = {7: 'read'};
  assert.equal(check(f.env, f.transport).artifact_id, 20);
  f.artifact.digest = 'sha256:' + 'd'.repeat(64);
  assert.throws(() => check(f.env, f.transport), /historical/);
});

test('the exact immutable archive digest is checked against downloaded bytes', () => {
  const crypto = require('node:crypto');
  const raw = Buffer.from('fixture archive bytes');
  const expected = 'sha256:' + crypto.createHash('sha256').update(raw).digest('hex');
  const env = {GITHUB_REPOSITORY: 'owner/repo'};
  const transport = (exe, argv) => {
    assert.equal(exe, 'gh');
    assert.equal(argv.at(-1), 'repos/owner/repo/actions/artifacts/20/zip');
    return raw;
  };
  verifyArchive(env, 20, expected, transport);
  assert.throws(() => verifyArchive(env, 20, 'sha256:' + '0'.repeat(64), transport), /digest mismatch/);
});

test('trusted dev importer verifies full inventory before writing separate staging', t => {
  const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
  const {canonicalInputFingerprint, perFileDigests} = require('../rebuild-docs.js');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'cg-legacy-pages-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const source = path.join(root, 'dev'), artifact = path.join(root, 'artifact'), staging = path.join(root, 'staging');
  for (const dir of [source, artifact]) fs.mkdirSync(path.join(dir, 'docs'), {recursive: true});
  fs.writeFileSync(path.join(root, 'stable.html'), 'stable remains unchanged');
  fs.writeFileSync(path.join(source, 'docs/index.html'), 'canonical dev content');
  fs.writeFileSync(path.join(artifact, 'docs/index.html'), 'canonical dev content');
  const metadata = {schemaVersion: 1, site: {files: perFileDigests(artifact),
    fingerprint: canonicalInputFingerprint(source).fingerprint}};
  fs.writeFileSync(path.join(artifact, '.docs-build-metadata.json'), JSON.stringify(metadata));
  fs.writeFileSync(path.join(artifact, 'docs/extra.html'), 'unlisted');
  assert.throws(() => importDev(source, artifact, staging), /file list/);
  assert.equal(fs.readFileSync(path.join(source, 'docs/index.html'), 'utf8'), 'canonical dev content');
  fs.rmSync(path.join(artifact, 'docs/extra.html'));
  assert.throws(() => importDev(source, artifact, staging), /unknown canonical producer/);
  assert.equal(fs.readFileSync(path.join(source, 'docs/index.html'), 'utf8'), 'canonical dev content');
  assert.equal(fs.existsSync(staging), false);
  assert.equal(fs.readFileSync(path.join(root, 'stable.html'), 'utf8'), 'stable remains unchanged');
});
