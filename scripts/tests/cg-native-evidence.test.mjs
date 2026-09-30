import assert from 'node:assert/strict';
import test from 'node:test';
import { acquire, passiveTools } from '../../.github/plugin-support/cg-native-evidence/evidence.mjs';
import { fixture, chain, sdkFixture, inputFor, rootID, childID, secret } from './native-evidence-fixture.mjs';

/** Execute passive acquisition against a factory-bound offline wire fixture. */
async function run(f = fixture(), child, client = sdkFixture(f.nativeFetch)) {
  return acquire(inputFor(client), f.context, child === undefined ? {} : { childID: child }, child !== undefined);
}

test('root identity uses current message agent, never mutable session selection', async () => {
  const f = fixture();
  const asks = [];
  f.context.ask = async (request) => asks.push(request);
  const result = await run(f);
  assert.equal(result.status, 'observed');
  assert.equal(result.self.agent, 'code');
  assert.equal(result.self.sessionID, rootID);
  assert.equal(result.qualification, 'unverified');
  assert.equal(result.parent, null);
  assert.deepEqual(asks, [{ permission: 'cg_native_identity', patterns: ['self'], always: [], metadata: {} }]);
  assert.ok(Buffer.byteLength(JSON.stringify(result)) <= 4096);
  assert.ok(!JSON.stringify(result).includes(secret));
});

test('child identity joins exact native parent part/call/message/target', async () => {
  const f = fixture();
  Object.assign(f.context, { sessionID: childID, messageID: 'msg_childcurrent', agent: 'cg-workflow-stage' });
  const result = await run(f);
  assert.equal(result.status, 'observed');
  assert.equal(result.parent.callID, 'call_dispatch');
  assert.equal(result.parent.partID, 'prt_dispatch');
  assert.equal(result.parent.messageID, 'msg_dispatch');
  assert.equal(result.parent.agent, 'code');
  assert.equal(result.parent.target, 'cg-workflow-stage');
});

test('observer accepts only independently joined native descendants', async () => {
  const f = fixture();
  const asks = [];
  f.context.ask = async (request) => asks.push(request);
  const result = await run(f, childID);
  assert.equal(result.status, 'observed');
  assert.equal(result.edges.length, 1);
  assert.equal(result.edges[0].childID, childID);
  assert.equal(result.qualification, 'unverified');
  assert.deepEqual(asks, [{ permission: 'cg_native_evidence', patterns: [childID], always: [], metadata: {} }]);
  assert.ok(!JSON.stringify(result).includes(secret));
  assert.ok(result.provenance.every((row) => /^[a-f0-9]{64}$/.test(row.sha256)));
});

for (const [name, mutate] of [
  ['spoofed context agent', (f) => { f.context.agent = 'cg-autopilot'; }],
  ['wrong current message', (f) => { f.context.messageID = 'msg_unknown'; }],
  ['settled current message', (f) => { f.records[rootID].messages[2].info.time.completed = 15; }],
  ['wrong worktree', (f) => { f.context.worktree += '/other'; }],
  ['wrong project', (f) => { f.records[rootID].session.projectID = 'another'; }],
  ['missing session identity', (f) => { delete f.records[rootID].session.id; }],
  ['missing parent metadata', (f) => { delete f.dispatch.parts[0].state.metadata; }],
  ['mismatched parent metadata', (f) => { f.dispatch.parts[0].state.metadata.parentSessionId = 'ses_other'; }],
  ['wrong child parent', (f) => { f.records[childID].session.parentID = 'ses_other'; }],
  ['wrong native target', (f) => { f.dispatch.parts[0].state.input.subagent_type = 'general'; }],
  ['missing call identity', (f) => { delete f.dispatch.parts[0].callID; }],
  ['wrong part session', (f) => { f.dispatch.parts[0].sessionID = 'ses_other'; }],
  ['wrong part message', (f) => { f.dispatch.parts[0].messageID = 'msg_other'; }],
  ['missing part ID', (f) => { delete f.dispatch.parts[0].id; }],
  ['unknown state', (f) => { f.dispatch.parts[0].state.status = 'unknown'; }],
  ['missing dispatch time', (f) => { delete f.dispatch.parts[0].state.time; }],
  ['impossible child creation time', (f) => { f.records[childID].session.time.created = 99; }],
  ['duplicate part', (f) => { f.dispatch.parts.push(structuredClone(f.dispatch.parts[0])); }],
  ['duplicate message', (f) => { f.records[rootID].messages.push(structuredClone(f.dispatch)); }],
  ['mention bypass', (f) => { f.records[rootID].messages[0].parts[0].type = 'agent'; }],
  ['subtask bypass', (f) => { f.records[rootID].messages[0].parts[0].type = 'subtask'; }],
  ['agent mismatch at dispatch', (f) => { f.dispatch.info.agent = 'general'; }],
  ['Task resume ambiguity', (f) => { f.dispatch.parts[0].state.input.task_id = childID; }],
]) {
  test(`fail closed: ${name}`, async () => {
    const f = fixture();
    mutate(f);
    const result = await run(f, childID);
    assert.equal(result.status, 'blocked');
    assert.match(result.reason, /^[a-z][a-z0-9-]+$/);
    assert.ok(!JSON.stringify(result).includes(secret));
  });
}

test('unknown target is not fetched merely because its ID was supplied', async () => {
  const f = fixture();
  const result = await run(f, 'ses_unowned');
  assert.equal(result.reason, 'not-owned-target');
  assert.ok(f.requests.every((request) => !request.url.includes('ses_unowned')));
});

test('self is not a descendant target', async () => {
  assert.equal((await run(fixture(), rootID)).reason, 'not-owned-target');
});

test('arbitrary identity arguments and invalid observer IDs are rejected before GET', async () => {
  const f = fixture();
  for (const [observer, args] of [[false, { parentID: rootID }], [true, { childID: '../auth' }],
    [true, { childID, extra: true }], [true, { childID: false }], [true, { childID: null }]]) {
    const result = await acquire(inputFor(sdkFixture(f.nativeFetch)), f.context, args, observer);
    assert.equal(result.reason, 'invalid-arguments');
  }
  assert.equal(f.requests.length, 0);
});

test('native permission denial is not overridden or copied into a result', async () => {
  const f = fixture();
  f.context.ask = async () => { throw new Error(secret); };
  const result = await run(f);
  assert.equal(result.reason, 'permission-denied');
  assert.equal(f.requests.length, 0);
  assert.ok(!JSON.stringify(result).includes(secret));
});

test('missing plugin context and cancelled acquisition add no authority', async () => {
  const f = fixture();
  delete f.context.messageID;
  assert.equal((await run(f)).status, 'blocked');
  const g = fixture();
  g.context.abort = AbortSignal.abort(secret);
  assert.equal((await run(g)).reason, 'cancelled');
  assert.equal(g.requests.length, 0);
});

test('unrelated root records cannot authenticate another caller', async () => {
  const f = fixture();
  f.records.ses_other = structuredClone(f.records[rootID]);
  f.records.ses_other.session.id = 'ses_other';
  for (const row of f.records.ses_other.messages) {
    row.info.sessionID = 'ses_other';
    row.parts = [];
  }
  f.context.sessionID = 'ses_other';
  const result = await run(f, childID);
  assert.equal(result.reason, 'not-owned-target');
  assert.ok(f.requests.every((request) => !new URL(request.url).pathname.includes(childID)));
});

test('declared identity tool cannot select observer mode through extra arguments', async () => {
  const f = fixture();
  const tool = (definition) => definition;
  tool.schema = { string: () => ({ regex: () => ({}) }) };
  const hooks = passiveTools(inputFor(sdkFixture(f.nativeFetch)), tool);
  assert.deepEqual(Object.keys(hooks), ['tool']);
  const result = JSON.parse(await hooks.tool.cg_native_identity.execute({ childID }, f.context));
  assert.equal(result.reason, 'invalid-arguments');
  assert.equal(f.requests.length, 0);
  const missing = JSON.parse(await hooks.tool.cg_native_evidence.execute({}, f.context));
  assert.equal(missing.reason, 'invalid-arguments');
});

test('identity rejects over-depth native ancestors rather than checking only one parent', async () => {
  const { f, ids } = chain(5);
  Object.assign(f.context, { sessionID: ids.at(-1), messageID: 'msg_current', agent: 'code' });
  assert.equal((await run(f)).reason, 'depth-limit');
});

test('descendant graphs enforce depth three and four-edge bounds', async () => {
  const { f, ids } = chain(5);
  assert.equal((await run(f, ids.at(-1))).reason, 'depth-limit');
});

test('native ancestor cycles are rejected', async () => {
  const { f } = chain(2);
  f.records[rootID].session.parentID = childID;
  f.records[childID].messages[1] = structuredClone(f.records[rootID].messages[1]);
  const row = f.records[childID].messages[1];
  row.info.sessionID = childID;
  row.parts[0].sessionID = childID;
  row.parts[0].state.metadata = { parentSessionId: childID, sessionId: rootID };
  assert.equal((await run(f)).status, 'blocked');
});

test('depth-three identity and descendant evidence fit their separate output caps', async () => {
  const { f, ids } = chain(4);
  const observed = await run(f, ids.at(-1));
  assert.equal(observed.status, 'observed');
  assert.equal(observed.edges.length, 3);
  assert.ok(Buffer.byteLength(JSON.stringify(observed)) <= 8192);
  Object.assign(f.context, { sessionID: ids.at(-1), agent: 'code' });
  const identity = await run(f);
  assert.equal(identity.status, 'observed');
  assert.ok(Buffer.byteLength(JSON.stringify(identity)) <= 4096);
});

test('observer cannot select its parent as an owned descendant', async () => {
  const f = fixture();
  Object.assign(f.context, { sessionID: childID, messageID: 'msg_childcurrent', agent: 'cg-workflow-stage' });
  assert.equal((await run(f, rootID)).reason, 'not-owned-target');
});

test('a padded native history cannot exceed the four-edge inventory cap', async () => {
  const f = fixture();
  for (let i = 0; i < 4; i++) {
    const part = structuredClone(f.dispatch.parts[0]);
    part.id = `prt_extra_${i}`; part.callID = `call_extra_${i}`;
    part.state.metadata.sessionId = `ses_extra_${i}`;
    f.dispatch.parts.push(part);
  }
  assert.equal((await run(f, childID)).reason, 'edge-limit');
  assert.ok(f.requests.every((request) => !request.url.includes('ses_extra')));
});
