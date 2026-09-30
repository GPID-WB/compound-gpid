import assert from 'node:assert/strict';
import test from 'node:test';
import { pathToFileURL } from 'node:url';
import { createReader, LIMITS } from '../../.github/plugin-support/cg-native-evidence/transport.mjs';
import { fixture, inputFor, rootID, secret } from './native-evidence-fixture.mjs';

// Missing/transitively broken explicit SDK installations are errors, never hidden skips.
const source = process.env.CG_NATIVE_EVIDENCE_SDK_CLIENT;
const sdk = await import(source ? pathToFileURL(source).href : '../../.kilo/node_modules/@kilocode/sdk/dist/client.js');
const clientFor = (fetch) => sdk.createKiloClient({ baseUrl: 'http://localhost:4096',
  directory: inputFor({}).directory, headers: { authorization: secret }, fetch });
const turn = () => new Promise((resolve) => setImmediate(resolve));

/** Run a reader on the actual installed SDK, but never on a native server. */
async function using(fetch, action, limits = LIMITS, signal = new AbortController().signal) {
  const reader = createReader(inputFor(clientFor(fetch)), signal, limits);
  try { return await action(reader); } finally { reader.close(); }
}

test('actual SDK preserves guarded Request identity, authentication and positive pagination', async () => {
  const f = fixture();
  await using(f.nativeFetch, async (r) => {
    assert.equal((await r.get(rootID)).id, rootID);
    assert.equal((await r.message(rootID, 'msg_current')).info.agent, 'code');
    assert.equal((await r.messages(rootID)).length, 3);
  });
  assert.equal(f.requests.length, 3);
  assert.ok(f.requests.every((r) => r.method === 'GET' && r.redirect === 'error' && r.headers.get('authorization') === secret));
  assert.equal(new URL(f.requests[2].url).searchParams.get('limit'), '50');
});

for (const status of [200, 401, 500]) {
  test(`actual SDK bounds status ${status} before its parser`, async () => {
    await assert.rejects(using(async () => new Response(secret.repeat(10), { status }),
      (r) => r.get(rootID), { ...LIMITS, responseBytes: 8 }), { message: 'evidence-too-large' });
  });
}

test('actual SDK preserves the in-process factory instead of using global fetch', async () => {
  const f = fixture(); const original = globalThis.fetch;
  globalThis.fetch = () => { throw new Error('No global transport'); };
  try { await using(f.nativeFetch, (r) => r.get(rootID)); }
  finally { globalThis.fetch = original; }
  assert.equal(f.requests.length, 1);
});

for (const link of ['</older>; rel=next', '</older>; rel = next', '</older>; rel="prev next"', '</older>; rel=prev']) {
  test(`actual SDK rejects nonempty Link without cursor: ${link}`, async () => {
    await assert.rejects(using(async () => Response.json([], { headers: { Link: link } }),
      (r) => r.messages(rootID)), { message: 'invalid-cursor' });
  });
}

test('actual SDK reconstructs cursor requests without following Link URLs', async () => {
  let count = 0;
  await using(async (request) => {
    if (++count === 1) return Response.json([], { headers: { 'X-Next-Cursor': 'page2', Link: '<https://unowned.invalid>; rel = next' } });
    assert.equal(new URL(request.url).origin, 'http://localhost:4096');
    assert.equal(new URL(request.url).searchParams.get('before'), 'page2');
    return Response.json([]);
  }, (r) => r.messages(rootID));
  assert.equal(count, 2);
});

test('actual SDK preflights all three method contracts before any native GET', async () => {
  let nativeCalls = 0; const probes = [];
  const client = clientFor(async () => { nativeCalls++; return Response.json({}); });
  const original = client.session.messages.bind(client.session);
  client.session.messages = (options) => {
    probes.push(typeof options.fetch);
    // Simulate an SDK without the requestValidator contract, but with public fetch override.
    return original({ ...options, requestValidator: undefined });
  };
  const reader = createReader(inputFor(client), new AbortController().signal);
  try { await assert.rejects(reader.get(rootID), { message: 'unsupported-sdk' }); }
  finally { reader.close(); }
  assert.deepEqual(probes, ['function']);
  assert.equal(nativeCalls, 0);
});

test('SDK with malformed override result is rejected before native I/O', async () => {
  const client = clientFor(() => { throw new Error('Native I/O forbidden'); });
  client.session.message = async () => null;
  const reader = createReader(inputFor(client), new AbortController().signal);
  try { await assert.rejects(reader.get(rootID), { message: 'unsupported-sdk' }); }
  finally { reader.close(); }
});

test('synchronous factory abort plus rejected promise never leaks an unhandled rejection', async () => {
  const controller = new AbortController();
  await assert.rejects(using(() => {
    controller.abort(); return Promise.reject(new Error('RAW_SENTINEL'));
  }, (r) => r.get(rootID), LIMITS, controller.signal), { message: 'cancelled' });
  await turn();
});

test('synchronous SDK operation abort still handles its rejected startup promise', async () => {
  const controller = new AbortController();
  const client = clientFor(() => { throw new Error('No native I/O'); });
  client.session.get = () => { controller.abort(); return Promise.reject(new Error('RAW_SDK_SENTINEL')); };
  const reader = createReader(inputFor(client), controller.signal);
  try { await assert.rejects(reader.get(rootID), { message: 'cancelled' }); await turn(); }
  finally { reader.close(); }
});

test('held stream reader abort handles rejected read and cleanup operations', async () => {
  const controller = new AbortController(); let cancelled = false; let released = false;
  const response = new Response(new ReadableStream({}));
  response.body.getReader = () => ({
    read() { controller.abort(); return Promise.reject(new Error('RAW_READ_SENTINEL')); },
    cancel() { cancelled = true; return Promise.reject(new Error('RAW_CANCEL_SENTINEL')); },
    releaseLock() { released = true; },
  });
  await assert.rejects(using(async () => response, (r) => r.get(rootID), LIMITS, controller.signal), { message: 'cancelled' });
  await turn();
  assert.equal(cancelled, true); assert.equal(released, true);
});

test('deadline cancels an already-held stalled body reader', async () => {
  let cancelled = false;
  await assert.rejects(using(async () => new Response(new ReadableStream({ cancel() { cancelled = true; } })),
    (r) => r.get(rootID), { ...LIMITS, milliseconds: 40 }), { message: 'deadline-exceeded' });
  await turn(); assert.equal(cancelled, true);
});

for (const termination of ['deadline', 'close']) for (const badCleanup of [false, true]) {
  test(`late actual SDK factory response is cancelled: ${termination}, cleanup rejects=${badCleanup}`, async () => {
    let deliver; let started; let cancelled = false;
    const ready = new Promise((resolve) => { started = resolve; });
    const pending = new Promise((resolve) => { deliver = resolve; });
    const reader = createReader(inputFor(clientFor(() => { started(); return pending; })),
      new AbortController().signal, { ...LIMITS, milliseconds: termination === 'deadline' ? 40 : 30000 });
    const result = reader.get(rootID);
    const rejected = assert.rejects(result, { message: termination === 'deadline' ? 'deadline-exceeded' : 'cancelled' });
    await ready;
    if (termination === 'close') reader.close();
    try {
      await rejected;
      deliver(new Response(new ReadableStream({ cancel() {
        cancelled = true; if (badCleanup) throw new Error('RAW_CLEANUP_SENTINEL');
      } })));
      await turn(); await turn();
      assert.equal(cancelled, true);
    } finally { reader.close(); }
  });
}

test('actual SDK never parses native JSON a second time', async () => {
  const client = clientFor(async () => Response.json({ ok: true }));
  const original = client.session.get.bind(client.session);
  let nativeOptions;
  client.session.get = (options) => { if (!options.fetch) nativeOptions = options; return original(options); };
  const reader = createReader(inputFor(client), new AbortController().signal);
  try { assert.equal((await reader.get(rootID)).ok, true); }
  finally { reader.close(); }
  assert.equal(nativeOptions.parseAs, 'stream');
});
