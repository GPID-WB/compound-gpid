import assert from 'node:assert/strict';
import test from 'node:test';
import { createReader, LIMITS } from '../../.github/plugin-support/cg-native-evidence/transport.mjs';
import { EvidenceError, parseWire } from '../../.github/plugin-support/cg-native-evidence/wire.mjs';
import { fixture, sdkFixture, inputFor, rootID, secret } from './native-evidence-fixture.mjs';

/** Close each request budget even when a negative case throws. */
async function readWith(fetch, action, limits, client) {
  const reader = createReader(inputFor(client ?? sdkFixture(fetch)), new AbortController().signal, limits);
  try { return await action(reader); } finally { reader.close(); }
}

test('fixed production acquisition caps', () => {
  assert.deepEqual(LIMITS, { page: 50, pages: 20, sessions: 5, edges: 4, depth: 3,
    responseBytes: 8 * 1024 * 1024, totalBytes: 32 * 1024 * 1024, milliseconds: 30000, nodes: 100000 });
});

test('SDK-generated Request retains internal factory authentication and directory', async () => {
  const f = fixture();
  await readWith(f.nativeFetch, async (r) => assert.equal((await r.get(rootID)).id, rootID));
  assert.equal(f.requests.length, 1);
  const request = f.requests[0];
  assert.equal(request.headers.get('authorization'), secret);
  assert.equal(request.redirect, 'error');
  assert.equal(request.method, 'GET');
  assert.equal(new URL(request.url).searchParams.get('directory'), inputFor({}).directory);
});

test('in-process factory binding is preserved instead of global fetch fallback', async () => {
  let calls = 0;
  const f = fixture();
  const original = globalThis.fetch;
  globalThis.fetch = () => { throw new Error('Global transport must never run'); };
  try {
    await readWith(async (request) => { calls++; return f.nativeFetch(request); }, (r) => r.get(rootID));
  } finally { globalThis.fetch = original; }
  assert.equal(calls, 1);
});

for (const status of [200, 400, 401, 404, 500]) {
  test(`raw status ${status} body is bounded before SDK parse`, async () => {
    let cancelled = false;
    const body = new ReadableStream({
      pull(controller) { controller.enqueue(new TextEncoder().encode(secret.repeat(2))); },
      cancel() { cancelled = true; },
    });
    await assert.rejects(readWith(async () => new Response(body, { status }), (r) => r.get(rootID),
      { ...LIMITS, responseBytes: 8 }), { message: 'evidence-too-large' });
    assert.equal(cancelled, true);
  });
}

for (const response of [null, undefined, {}, 'raw-secret']) {
  test(`invalid raw response ${typeof response} fails closed`, async () => {
    await assert.rejects(readWith(async () => response, (r) => r.get(rootID)), { message: 'invalid-response' });
  });
}

for (const status of [204, 206, 302, 401, 500]) {
  test(`non-evidence HTTP status ${status} has a closed error`, async () => {
    await assert.rejects(readWith(async () => new Response(status === 204 ? null : secret, { status }),
      (r) => r.get(rootID)), { message: status >= 300 && status < 400 ? 'redirect-denied' : 'http-error' });
  });
}

test('aggregate bound survives multiple requests', async () => {
  await assert.rejects(readWith(async () => new Response('{"ok":true}'), async (r) => {
    await r.get(rootID); await r.message(rootID, 'msg_current');
  }, { ...LIMITS, totalBytes: 12 }), { message: 'evidence-too-large' });
});

test('a sixth distinct session is rejected before its GET', async () => {
  let calls = 0;
  await assert.rejects(readWith(async () => { calls++; return Response.json({}); }, async (r) => {
    for (let i = 0; i < 6; i++) await r.get(`ses_${i}`);
  }), { message: 'session-limit' });
  assert.equal(calls, 5);
});

test('unavailable public SDK methods fail without a transport substitution', () => {
  assert.throws(() => createReader(inputFor({ session: {} }), new AbortController().signal), { message: 'unsupported-sdk' });
});

test('request deadline bounds a factory fetch that ignores abort', async () => {
  await assert.rejects(readWith(() => new Promise(() => {}), (r) => r.get(rootID),
    { ...LIMITS, milliseconds: 10 }), { message: 'deadline-exceeded' });
});

test('cancellation bounds a stalled body and discards its reason', async () => {
  const controller = new AbortController();
  const reader = createReader(inputFor(sdkFixture(async () => new Response(new ReadableStream({})))), controller.signal);
  const promise = reader.get(rootID);
  controller.abort(secret);
  try { await assert.rejects(promise, { message: 'cancelled' }); } finally { reader.close(); }
});

test('foreign factory origin is rejected before dispatch', async () => {
  const f = fixture();
  await assert.rejects(readWith(f.nativeFetch, (r) => r.get(rootID), undefined,
    sdkFixture(f.nativeFetch, { origin: 'https://unowned.invalid' })), { message: 'unsupported-transport' });
  assert.equal(f.requests.length, 0);
});

test('pagination is positive, bounded, cursor-only and complete', async () => {
  let pages = 0;
  await readWith(async (request) => {
    const url = new URL(request.url);
    assert.equal(url.searchParams.get('limit'), '50');
    if (++pages === 1) return Response.json([], { headers: { 'X-Next-Cursor': 'cursor_2' } });
    assert.equal(url.searchParams.get('before'), 'cursor_2');
    return Response.json([]);
  }, (r) => r.messages(rootID));
  assert.equal(pages, 2);
});

test('partial pagination cannot report absence after the page cap', async () => {
  let pages = 0;
  await assert.rejects(readWith(async () => Response.json([], { headers: { 'X-Next-Cursor': `cursor_${++pages}` } }),
    (r) => r.messages(rootID), { ...LIMITS, pages: 2 }), { message: 'history-limit' });
  assert.equal(pages, 2);
});

test('duplicate and URL cursors fail instead of replaying or following Link', async () => {
  for (const cursor of ['repeat', 'https://unowned.invalid']) {
    await assert.rejects(readWith(async () => Response.json([], { headers: { 'X-Next-Cursor': cursor } }),
      (r) => r.messages(rootID)), { message: 'invalid-cursor' });
  }
});

for (const text of ['{"id":1,"id":2}', '{"x":{"id":1,"\\u0069d":2}}', 'null', '{"x":1e999}', '[1,]',
  '{"x":true} trailing', '['.repeat(70) + '0' + ']'.repeat(70)]) {
  test(`strict wire rejection ${text.slice(0, 30)}`, () => assert.throws(() => parseWire(text)));
}

test('unsupported validator contract makes zero native fetch calls', async () => {
  const f = fixture();
  const client = sdkFixture(f.nativeFetch, { validator: false });
  await assert.rejects(readWith(null, (r) => r.get(rootID), undefined, client), { message: 'unsupported-sdk' });
  assert.equal(f.requests.length, 0);
});

test('remaining byte budget zero rejects before another SDK call', async () => {
  let calls = 0;
  await assert.rejects(readWith(async () => { calls++; return new Response('{}'); }, async (r) => {
    await r.get(rootID); await r.get('ses_next');
  }, { ...LIMITS, totalBytes: 2 }), { message: 'evidence-too-large' });
  assert.equal(calls, 1);
});

test('parse node budget is shared and checked before allocation', () => {
  const budget = { remaining: 3, check: () => {} };
  parseWire('[{}]', { budget });
  assert.equal(budget.remaining, 1);
  assert.throws(() => parseWire('[{}]', { budget }), { message: 'node-limit' });
  assert.equal(budget.remaining, 0);
});

test('message parser rejects item 51 before parsing its value', () => {
  const budget = { remaining: 1000, check: () => {} };
  const text = '[' + '{},'.repeat(50) + '{INVALID_UNPARSED}]';
  assert.throws(() => parseWire(text, { budget, maxRootItems: 50 }), { message: 'invalid-page' });
  assert.equal(budget.remaining, 949);
});

test('small object amplification and periodic parse deadline checks are bounded', () => {
  const text = JSON.stringify(Array.from({ length: 1000 }, () => ({})));
  assert.throws(() => parseWire(text, { budget: { remaining: 100, check: () => {} } }), { message: 'node-limit' });
  let checks = 0;
  assert.throws(() => parseWire(text, { budget: { remaining: 10000, check: () => {
    if (++checks === 3) throw new EvidenceError('deadline-exceeded');
  } } }), { message: 'deadline-exceeded' });
});

test('transport shares its node budget across native responses', async () => {
  await assert.rejects(readWith(async () => new Response('[{}]'), async (r) => {
    await r.get(rootID); await r.message(rootID, 'msg_current');
  }, { ...LIMITS, nodes: 3 }), { message: 'node-limit' });
});
