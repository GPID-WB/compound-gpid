import assert from 'node:assert/strict';
import test from 'node:test';
import { acquire } from '../../.github/plugin-support/cg-native-evidence/evidence.mjs';
import { fixture, chain, sdkFixture, inputFor, rootID, childID } from './native-evidence-fixture.mjs';

/** Run only passive ownership acquisition against native-shaped fixtures. */
const observe = (f, fetch = f.nativeFetch) => acquire(inputFor(sdkFixture(fetch)), f.context, { childID }, true);

for (const taskID of [false, 0, null, [], {}, ' ', childID]) {
  test(`present non-fresh task_id is rejected: ${JSON.stringify(taskID)}`, async () => {
    const f = fixture(); f.dispatch.parts[0].state.input.task_id = taskID;
    assert.equal((await observe(f)).reason, 'reused-task');
  });
}

test('absent and explicitly empty string task_id both mean fresh dispatch', async () => {
  for (const present of [false, true]) {
    const f = fixture();
    if (present) f.dispatch.parts[0].state.input.task_id = '';
    assert.equal((await observe(f)).status, 'observed');
  }
});

test('earliest child-user ties block regardless of response order or agent', async () => {
  for (const agent of ['general', 'cg-workflow-stage']) for (const reverse of [false, true]) {
    const f = fixture(); const rows = f.records[childID].messages;
    const other = structuredClone(rows[0]); other.info.id = 'msg_tie'; other.info.agent = agent;
    other.parts = [];
    rows.push(other); if (reverse) rows.reverse();
    assert.equal((await observe(f)).reason, 'initial-message-ambiguous');
  }
});

for (const [name, mutate] of [
  ['child user predates child', (f) => { f.records[childID].messages[0].info.time.created = 10; }],
  ['child assistant predates child', (f) => { f.records[childID].messages[1].info.time.created = 11; }],
  ['completion predates session', (f) => { f.records[childID].messages[1].info.time.completed = 1; }],
  ['dispatch user follows assistant', (f) => { f.records[rootID].messages[0].info.time.created = 15; }],
  ['Task starts before assistant', (f) => { f.dispatch.parts[0].state.time.start = 10; }],
  ['child predates Task', (f) => { f.records[childID].session.time.created = 10; }],
  ['child follows settled Task', (f) => { f.dispatch.parts[0].state.time.end = 11; }],
]) {
  test(`chronology contradiction blocks: ${name}`, async () => {
    const f = fixture(); mutate(f);
    assert.equal((await observe(f)).status, 'blocked');
  });
}

for (const mutation of ['missing', 'agent', 'role', 'created', 'parentID']) {
  test(`complete history reconciles exact current identity: ${mutation}`, async () => {
    const f = fixture();
    const fetch = async (request) => {
      if (new URL(request.url).pathname === `/session/${rootID}/message`) {
        const rows = structuredClone(f.records[rootID].messages);
        const item = rows[2];
        if (mutation === 'missing') rows.pop();
        if (mutation === 'agent') item.info.agent = 'general';
        if (mutation === 'role') item.info.role = 'user';
        if (mutation === 'created') item.info.time.created = 12;
        if (mutation === 'parentID') item.info.parentID = 'msg_other';
        return Response.json(rows);
      }
      return f.nativeFetch(request);
    };
    assert.equal((await observe(f, fetch)).reason, 'current-history-mismatch');
  });
}

test('mutable parts/completion do not change immutable current identity', async () => {
  const f = fixture();
  const fetch = async (request) => {
    if (new URL(request.url).pathname === `/session/${rootID}/message`) {
      const rows = structuredClone(f.records[rootID].messages);
      rows[2].info.time.completed = 20;
      rows[2].parts.push({ id: 'prt_later', type: 'text', sessionID: rootID, messageID: 'msg_current', text: 'later' });
      return Response.json(rows);
    }
    return f.nativeFetch(request);
  };
  assert.equal((await observe(f, fetch)).status, 'observed');
});

test('inspected edges are charged across ancestor histories before target searches', async () => {
  const { f, ids } = chain(4);
  for (const sid of ids.slice(0, 2)) {
    const part = structuredClone(f.records[sid].messages[1].parts[0]);
    part.id = `prt_extra_${sid}`; part.callID = `call_extra_${sid}`;
    part.state.metadata.sessionId = `ses_unused_${sid}`;
    f.records[sid].messages[1].parts.push(part);
  }
  f.context.sessionID = ids.at(-1);
  const result = await acquire(inputFor(sdkFixture(f.nativeFetch)), f.context, {});
  assert.equal(result.reason, 'edge-limit');
  assert.ok(f.requests.every((request) => !request.url.includes('ses_unused')));
});

test('revisiting cached histories does not charge an edge twice', async () => {
  const { f, ids } = chain(4); f.context.sessionID = childID;
  const result = await acquire(inputFor(sdkFixture(f.nativeFetch)), f.context, { childID: ids.at(-1) }, true);
  assert.equal(result.status, 'observed');
  assert.equal(result.edges.length, 2);
});

test('overlapping sibling intervals are not mistaken for a native chronology contradiction', async () => {
  const f = fixture(); const sid = 'ses_sibling';
  const sibling = structuredClone(f.records[childID]); sibling.session.id = sid;
  for (const row of sibling.messages) {
    row.info.sessionID = sid; row.info.id += '_sibling';
    if (row.info.parentID) row.info.parentID += '_sibling';
    for (const part of row.parts) { part.id += '_sibling'; part.sessionID = sid; part.messageID = row.info.id; }
  }
  f.records[sid] = sibling;
  const part = structuredClone(f.dispatch.parts[0]);
  part.id = 'prt_sibling'; part.callID = 'call_sibling'; part.state.metadata.sessionId = sid;
  f.dispatch.parts.push(part);
  const result = await observe(f);
  assert.equal(result.status, 'observed'); assert.equal(result.edges.length, 1);
  assert.ok(f.requests.some((request) => new URL(request.url).pathname === `/session/${sid}`));
});

test('incomplete sibling evidence blocks despite a valid selected child', async () => {
  const f = fixture(); const part = structuredClone(f.dispatch.parts[0]);
  part.id = 'prt_incomplete'; part.callID = 'call_incomplete'; delete part.state.metadata;
  f.dispatch.parts.push(part);
  assert.equal((await observe(f)).reason, 'incomplete-task');
});
