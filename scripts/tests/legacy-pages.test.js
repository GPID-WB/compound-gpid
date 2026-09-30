"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const { check, verifyArchive, importDev } = require('../legacy-pages.js');
const {readOfficial, restoreOfficial, sealOfficial, stampPreview, recheckOfficial, FILE} = require('../legacy-official-snapshot.js');

test('preview imports verified official docs rather than validating a moving main tree', () => {
  const fs = require('node:fs'), path = require('node:path');
  const root = path.resolve(__dirname, '../..');
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/release-pages.yml'), 'utf8');
  assert.ok(workflow.includes('node scripts/legacy-pages.js restore-official official-source official-state.json'));
  assert.ok(workflow.includes('node scripts/legacy-pages.js seal-official release-source release-artifact'));
  assert.ok(!workflow.includes('ref: main'));
  assert.ok(workflow.includes('node scripts/legacy-pages.js recheck-official official-state.json'));
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
    if (!endpoint) value = {id: 123, full_name: 'owner/repo', default_branch: 'production', fork: false};
    else if (endpoint === '/branches/production') value = {name: 'production', protected: state.protected, commit: {sha}};
    else if (endpoint === '/branches/production/protection') {
      if (state.denyAdministration) throw Object.assign(Error('administration unavailable'), {stdout: 'HTTP/2.0 403 Forbidden\n\n{}'});
      value = {enforce_admins: {enabled: true}, allow_force_pushes: {enabled: false}, allow_deletions: {enabled: false}, required_pull_request_reviews: {required_approving_review_count: 1, dismiss_stale_reviews: true, bypass_pull_request_allowances: {users: [], teams: [], apps: []}}};
    }
    else if (endpoint === '/contents/.release-controller.json?ref=' + sha) value = {type: 'file', encoding: 'base64', content: Buffer.from(JSON.stringify({enabled: state.enabled, production_branches: ['deploy/2.x']})).toString('base64')};
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

function officialFixture(t) {
  const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
  const {buildSnapshot, exportSnapshot} = require('../docs-snapshots.js');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'cg-official-preview-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  function source(name) {
    const dir = path.join(root, name);
    fs.mkdirSync(path.join(dir, 'docs/assets'), {recursive: true});
    for (const [file, content] of Object.entries({'index.html': `<html><body>${name}</body></html>`,
      'navigation.json': '{"schemaVersion":"compound-gpid-docs-navigation-v1","groups":[]}',
      'assets/site.css': 'body {}', 'assets/site.js': '// site', '.nojekyll': ''})) fs.writeFileSync(path.join(dir, 'docs', file), content);
    return dir;
  }
  const officialSource = source('official-v2');
  buildSnapshot({root: officialSource, out: path.join(root, 'snapshot'), kind: 'release', tag: 'v2.0.0', sha: 'c'.repeat(40), runId: 11, runAttempt: 1});
  exportSnapshot(path.join(root, 'snapshot'), path.join(root, 'envelope.json'));
  const f = fixture(), original = f.transport, sha = 'c'.repeat(40);
  f.env.GITHUB_RUN_ID = '200'; f.env.GITHUB_RUN_ATTEMPT = '1'; f.env.GITHUB_REF_NAME = 'production'; f.env.GITHUB_JOB = 'deploy-dev';
  const currentPublisher = {runId: 50, runAttempt: 1, sha: f.env.GITHUB_SHA, branch: 'production', job: 'deploy'};
  f.state.value = {schemaVersion: 1, repositoryId: 123, officialBranch: 'deploy/2.x', publisher: {...currentPublisher},
    official: JSON.parse(fs.readFileSync(path.join(root, 'envelope.json')))};
  f.state.currentPublisher = currentPublisher;
  f.state.oldArtifactsExpired = false; f.state.sourceAdvanced = false; f.state.unrelatedRuns = 0;
  f.state.pages = {html_url: 'https://owner.github.io/repo/', cname: null, build_type: 'workflow'};
  const build = {...f.run, id: 11, head_sha: sha, head_branch: 'v2.0.0', path: '.github/workflows/release-docs.yml'};
  const artifact = {...f.artifact, id: 21, name: 'release-docs-site', workflow_run: {id: 11, head_sha: sha}};
  f.transport = (exe, args, options) => {
    if (exe === 'curl') {
      assert.equal(args[0], '--disable');
      assert.ok(args.includes('--proto')); assert.ok(args.includes('=https'));
      assert.ok(!args.some(arg => arg.includes('Authorization')));
      assert.match(args.at(-1), /^https:\/\/owner.github.io\/repo\/cg-official-snapshot.json\?verify=/);
      return Buffer.from(JSON.stringify(f.state.value) + '\n');
    }
    const endpoint = args.at(-1).replace('repos/owner/repo', '');
    const p = f.state.currentPublisher;
    let value;
    if (endpoint === '/pages') value = f.state.pages;
    else if (endpoint.startsWith('/deployments?')) value = [
      ...(f.state.pendingDeployment ? [{id: 71, environment: 'github-pages', sha: p.sha, ref: p.branch}] : []),
      {id: 70, environment: 'github-pages', sha: p.sha, ref: p.branch}];
    else if (endpoint === '/deployments/71/statuses?per_page=100') value = [{state: f.state.pendingDeployment}];
    else if (endpoint === '/deployments/70/statuses?per_page=100') value = [{state: 'success', log_url: `https://github.com/owner/repo/actions/runs/${p.runId}/job/60`}];
    else if (endpoint === '/actions/jobs/60') value = {id: 60, run_id: p.runId, run_attempt: p.runAttempt, head_sha: p.sha,
      name: p.job, status: 'completed', conclusion: 'success', steps: [{name: p.job === 'deploy' ? 'Deploy to GitHub Pages' : 'Deploy development preview to GitHub Pages', conclusion: 'success'}]};
    else if (endpoint === `/actions/runs/${p.runId}/attempts/${p.runAttempt}`) value = {id: p.runId, run_attempt: p.runAttempt,
      repository: {id: 123}, event: 'workflow_run', head_sha: p.sha, head_branch: p.branch, path: '.github/workflows/release-pages.yml', status: 'completed', conclusion: 'success'};
    else if (endpoint === '/actions/runs/11') { assert.ok(!f.state.oldArtifactsExpired); value = build; }
    else if (endpoint === '/actions/runs/11/artifacts?per_page=100&page=1') { assert.ok(!f.state.oldArtifactsExpired); value = {total_count: 1, artifacts: [artifact]}; }
    else if (endpoint === '/branches/deploy%2F2.x') value = {name: 'deploy/2.x', commit: {sha}};
    else if (endpoint.startsWith('/compare/')) {
      const [base, head] = endpoint.slice('/compare/'.length).split('...');
      value = {base_commit: {sha: base}, merge_base_commit: {sha: base === head ? base : 'd'.repeat(40)}, status: base === head ? 'identical' : 'diverged'};
    } else if (endpoint.startsWith('/contents/releases/')) { assert.ok(!f.state.sourceAdvanced); value = {type: 'file', encoding: 'base64', content: Buffer.from(JSON.stringify({tag: 'v2.0.0'})).toString('base64')}; }
    else return original(exe, args, options);
    assert.equal(exe, 'gh'); assert.ok(args.includes('GET'));
    f.state.calls.push(endpoint);
    return 'HTTP/2.0 200 OK\n\n' + JSON.stringify(value);
  };
  return {...f, root, source, officialSource};
}

test('durable official bytes survive artifact expiry, more than 100 runs and source payload advancement', t => {
  const f = officialFixture(t);
  f.state.oldArtifactsExpired = true; f.state.sourceAdvanced = true; f.state.unrelatedRuns = 1000;
  const selected = readOfficial(f.env, f.transport).value;
  assert.equal(selected.officialBranch, 'deploy/2.x');
  assert.equal(selected.official.record.sha, 'c'.repeat(40));
  assert.equal(selected.official.record.runId, 11);
  assert.ok(!f.state.calls.includes('/branches/main'));
  assert.ok(!f.state.calls.some(call => call.includes('/actions/workflows/') || call.includes('/contents/releases/') || call.includes('/actions/runs/11')));
});

test('untrusted, stale, corrupt or foreign durable state cannot authorize a preview', t => {
  for (const mutate of [f => {f.state.value.repositoryId++;}, f => {f.state.value.publisher.runId++;},
    f => {f.state.value.official.files['index.html'] = Buffer.from('substitution').toString('base64');},
    f => {f.state.currentPublisher.branch = 'feature/untrusted';}, f => {f.state.currentPublisher.runId++;},
    f => {f.state.pages.html_url = 'https://evil.invalid/repo/';}]) {
    const f = officialFixture(t); mutate(f);
    assert.throws(() => readOfficial(f.env, f.transport));
  }
});

test('a pending or failed deployment does not replace the durable official state', t => {
  const f = officialFixture(t);
  for (const state of ['in_progress', 'failure']) {
    f.state.pendingDeployment = state;
    assert.equal(readOfficial(f.env, f.transport).value.official.record.tag, 'v2.0.0');
  }
});

test('stable deploy then dev payload preview preserves every official site byte', t => {
  const fs = require('node:fs'), path = require('node:path');
  const {writeCombinedSite, digestTree} = require('../assemble-docs-site.js');
  const f = officialFixture(t), {root} = f, dev = f.source('dev');
  const args = {mainRoot: f.officialSource, devRoot: dev, mainSha: 'c'.repeat(40), devSha: 'b'.repeat(40),
    mainBranch: 'deploy/2.x', mainRef: 'v2.0.0'};
  writeCombinedSite({...args, out: path.join(root, 'stable-deploy')});
  const beforeLive = JSON.stringify(f.state.value);
  sealOfficial({...f.env, GITHUB_RUN_ID: '50', GITHUB_JOB: 'deploy', LEGACY_MODE: 'release', BUILD_RUN_ID: '11', RELEASE_BRANCH: 'deploy/2.x'},
    f.officialSource, path.join(root, 'stable-deploy'), f.transport);
  assert.equal(JSON.stringify(f.state.value), beforeLive, 'preparation cannot publish official state');
  f.state.value = JSON.parse(fs.readFileSync(path.join(root, 'stable-deploy/site', FILE)));
  f.state.oldArtifactsExpired = true; f.state.sourceAdvanced = true; f.state.unrelatedRuns = 1000;
  const restored = path.join(root, 'restored'), stateFile = path.join(root, 'official-state.json');
  restoreOfficial(f.env, restored, stateFile, f.transport);
  fs.writeFileSync(path.join(dev, 'docs/index.html'), '<html><body>new dev payload preview</body></html>');
  writeCombinedSite({...args, mainRoot: restored, devSha: 'e'.repeat(40), out: path.join(root, 'preview')});
  stampPreview(f.env, stateFile, path.join(root, 'preview'));
  recheckOfficial(f.env, stateFile, f.transport);
  const before = digestTree(path.join(root, 'stable-deploy/site')), after = digestTree(path.join(root, 'preview/site'));
  for (const file of Object.keys(f.state.value.official.record.files)) assert.equal(after[file], before[file], file);
  assert.notEqual(after['dev/index.html'], before['dev/index.html']);
  const previewValue = JSON.parse(fs.readFileSync(path.join(root, 'preview/site', FILE)));
  assert.deepEqual(previewValue.official, f.state.value.official);
  assert.equal(previewValue.publisher.job, 'deploy-dev');
  f.state.value = previewValue; f.state.currentPublisher = {...previewValue.publisher};
  assert.deepEqual(readOfficial(f.env, f.transport).value.official, previewValue.official);
  assert.throws(() => recheckOfficial(f.env, stateFile, f.transport), /state changed/);
});

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
  f.run.path = '.github/workflows/release-docs.yml'; f.run.head_branch = 'v1.2.0';
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

test('prerelease full-site deployment is denied independently of source branch eligibility', () => {
  const f = fixture();
  f.env.LEGACY_MODE = 'release';
  f.run.path = '.github/workflows/release-docs.yml'; f.run.head_branch = 'v1.2.0.9015';
  f.artifact.name = 'release-docs-site';
  assert.throws(() => check(f.env, f.transport), /prerelease full-site deployment is disabled/);
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
