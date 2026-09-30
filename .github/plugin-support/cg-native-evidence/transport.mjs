import { EvidenceError, requireEvidence, safeID, digest, parseWire } from './wire.mjs';

export const LIMITS = Object.freeze({ page: 50, pages: 20, sessions: 5, edges: 4, depth: 3,
  responseBytes: 8 * 1024 * 1024, totalBytes: 32 * 1024 * 1024, milliseconds: 30000, nodes: 100000 });

/**
 * Make an acquisition-scoped reader from trusted PluginInput and context.abort.
 * Input must supply the public SDK client, serverUrl and bound directory. Limits
 * are internal/test settings, never tool arguments. Methods return parsed native
 * records or throw closed errors; provenance contains no raw bodies or headers.
 * Always close in finally: const r = createReader(input, context.abort);
 * try { return await r.get(sessionID); } finally { r.close(); }
 * The cooperative deadline starts here, AFTER permission approval. It stops
 * waiting; it does not forcibly terminate ignored aborts or synchronous parsing.
 */
export function createReader(input, signal, limits = LIMITS) {
  const origin = new URL(input.serverUrl);
  requireEvidence(['http:', 'https:'].includes(origin.protocol) && !origin.username && !origin.password &&
    origin.pathname === '/' && !origin.search && !origin.hash, 'unsupported-transport');
  requireEvidence(['get', 'message', 'messages'].every((name) =>
    typeof input.client?.session?.[name] === 'function'), 'unsupported-sdk');
  const controller = new AbortController();
  let reason = 'cancelled';
  const cancel = () => controller.abort();
  signal.addEventListener('abort', cancel, { once: true });
  if (signal.aborted) cancel();
  const timer = setTimeout(() => { reason = 'deadline-exceeded'; cancel(); }, limits.milliseconds);
  const provenance = [];
  const sessions = new Set();
  let total = 0;
  let pages = 0;
  const deadline = performance.now() + limits.milliseconds;
  const check = () => {
    if (performance.now() >= deadline) { reason = 'deadline-exceeded'; cancel(); }
    requireEvidence(!controller.signal.aborted, reason);
  };
  const quietly = (operation) => { try { Promise.resolve(operation()).catch(() => {}); } catch {} };
  const dispose = (response) => { if (response instanceof Response) return response.body?.cancel(); };
  const wait = (operation, lateCleanup = () => {}) => new Promise((resolve, reject) => {
    try { check(); } catch (error) { reject(error); return; }
    let settled = false;
    const finish = (ok, value) => {
      if (settled) return;
      settled = true;
      controller.signal.removeEventListener('abort', onAbort);
      if (ok) resolve(value); else reject(value);
    };
    const onAbort = () => finish(false, new EvidenceError(reason));
    controller.signal.addEventListener('abort', onAbort, { once: true });
    if (controller.signal.aborted) { onAbort(); return; }
    try {
      // Attach handlers even if startup synchronously aborts and returns a rejection.
      Promise.resolve(operation()).then((value) => {
        if (!settled) { try { check(); } catch (error) { finish(false, error); } }
        if (settled) quietly(() => lateCleanup(value)); else finish(true, value);
      }, (error) => finish(false, error));
    } catch (error) { finish(false, error); }
  });
  const boundOptions = (options) => requireEvidence(typeof options.fetch === 'function' &&
    new URL(options.baseUrl).href === origin.href && options.method === 'GET', 'unsupported-transport');
  const boundRequest = (req, path, query) => {
    requireEvidence(req instanceof Request, 'unsupported-transport');
    const url = new URL(req.url);
    requireEvidence(url.origin === origin.origin && url.pathname === path && !url.hash &&
      !url.username && !url.password && req.method === 'GET' && req.body === null &&
      req.redirect === 'error' && [...url.searchParams].length === Object.keys(query).length &&
      Object.entries(query).every(([key, value]) => url.searchParams.get(key) === String(value)), 'unsupported-transport');
  };
  let proof;
  const prove = async () => {
    // Trust the public per-request fetch override, not an arbitrary hostile SDK.
    // Every method must prove validator-before-fetch and mutable request options
    // on an isolated synthetic transport BEFORE any factory/native GET is allowed.
    for (const kind of ['get', 'message', 'messages']) {
      const id = 'ses_cg_native_capability';
      const messageID = kind === 'message' ? 'msg_cg_native_capability' : undefined;
      const path = `/session/${id}` + (kind === 'get' ? '' : '/message') + (messageID ? `/${messageID}` : '');
      const query = { directory: input.directory, ...(kind === 'messages' ? { limit: limits.page } : {}) };
      let validated = false; let wrapped = false; let calls = 0; let response;
      const isolated = (req) => {
        boundRequest(req, path, query); calls++;
        response = new Response(null);
        return response;
      };
      try {
        const result = await wait(() => input.client.session[kind]({
          path: { id, ...(messageID ? { messageID } : {}) }, query, fetch: isolated,
          signal: controller.signal, redirect: 'error', parseAs: 'stream', responseStyle: 'fields', throwOnError: false,
          requestValidator: async (options) => {
            boundOptions(options);
            requireEvidence(!validated && options.fetch === isolated, 'unsupported-sdk');
            validated = true;
            options.fetch = (req) => { wrapped = true; return isolated(req); };
          },
        }), (result) => dispose(result?.response));
        requireEvidence(validated && wrapped && calls === 1 && result?.response === response &&
          result.data === null && !result.error, 'unsupported-sdk');
      } catch (error) {
        throw error instanceof EvidenceError ? error : new EvidenceError('unsupported-sdk');
      }
    }
  };
  const parseBudget = { remaining: limits.nodes, check };
  const request = async (kind, id, messageID, before) => {
    check(); safeID(id, 'ses_');
    if (messageID !== undefined) safeID(messageID, 'msg_');
    requireEvidence(total < limits.totalBytes, 'evidence-too-large');
    sessions.add(id);
    requireEvidence(sessions.size <= limits.sessions, 'session-limit');
    await (proof ??= prove());
    check();
    const path = `/session/${id}` + (kind === 'get' ? '' : '/message') + (messageID ? `/${messageID}` : '');
    const query = { directory: input.directory, ...(kind === 'messages' ? { limit: limits.page, ...(before ? { before } : {}) } : {}) };
    let guarded = false;
    let acquired = false;
    let data; let boundedResponse;
    const result = await wait(() => input.client.session[kind]({
      path: { id, ...(messageID ? { messageID } : {}) }, query,
      signal: controller.signal, redirect: 'error', parseAs: 'stream', responseStyle: 'fields', throwOnError: false,
      // Public requestValidator receives merged request options before Request construction.
      // Preserve the factory fetch, including in-process app.fetch; never inspect _client.
      requestValidator: async (options) => {
        boundOptions(options);
        requireEvidence(!guarded, 'unsupported-transport');
        guarded = true;
        const factoryFetch = options.fetch;
        options.fetch = async (req) => {
          check();
          requireEvidence(!acquired, 'unsupported-transport');
          boundRequest(req, path, query);
          acquired = true;
          const response = await wait(() => factoryFetch(req), dispose);
          requireEvidence(response instanceof Response, 'invalid-response');
          if (response.redirected || (response.status >= 300 && response.status < 400)) {
            quietly(() => dispose(response));
            throw new EvidenceError('redirect-denied');
          }
          const stream = response.body?.getReader();
          let bytes = 0;
          const storage = Buffer.allocUnsafe(Math.min(limits.responseBytes, limits.totalBytes - total));
          try {
            const length = response.headers.get('content-length');
            if (length !== null) {
              requireEvidence(/^\d+$/.test(length), 'invalid-response');
              requireEvidence(Number(length) <= limits.responseBytes && Number(length) + total <= limits.totalBytes, 'evidence-too-large');
            }
            if (stream) while (true) {
              const chunk = await wait(() => stream.read());
              if (chunk.done) break;
              requireEvidence(chunk.value instanceof Uint8Array, 'invalid-response');
              bytes += chunk.value.byteLength; total += chunk.value.byteLength;
              requireEvidence(bytes <= limits.responseBytes && total <= limits.totalBytes, 'evidence-too-large');
              storage.set(chunk.value, bytes - chunk.value.byteLength);
            }
          } finally {
            if (stream) { quietly(() => stream.cancel()); quietly(() => stream.releaseLock()); }
          }
          requireEvidence(response.status === 200, 'http-error');
          const buffer = storage.subarray(0, bytes);
          let text;
          try { text = new TextDecoder('utf-8', { fatal: true }).decode(buffer); }
          catch { throw new EvidenceError('invalid-json'); }
          const cursor = response.headers.get('x-next-cursor');
          const link = response.headers.get('link');
          // This native API uses X-Next-Cursor, not Link. Unknown Link-only history is incomplete.
          requireEvidence(!link?.trim() || cursor !== null, 'invalid-cursor');
          if (cursor !== null) requireEvidence(/^[A-Za-z0-9_-]{1,512}={0,2}$/.test(cursor), 'invalid-cursor');
          data = parseWire(text, { budget: parseBudget, maxRootItems: kind === 'messages' ? limits.page : undefined });
          provenance.push({ sessionID: id, messageID: messageID ?? null, kind, bytes,
            sha256: digest(buffer), at: Date.now() });
          // Stream mode gives the SDK an empty acknowledgement, not a second JSON parse.
          boundedResponse = new Response(null, { headers: cursor === null ? {} : { 'x-next-cursor': cursor } });
          return boundedResponse;
        };
      },
    }), (result) => dispose(result?.response));
    check();
    requireEvidence(guarded && acquired && result?.response === boundedResponse &&
      result.response?.status === 200 && !result.error && result.data === null && data !== undefined, 'unsupported-sdk');
    return { data, response: boundedResponse };
  };
  return {
    limits, provenance, check,
    get: async (id) => (await request('get', id)).data,
    message: async (id, messageID) => (await request('message', id, messageID)).data,
    messages: async (id) => {
      const result = [];
      const seen = new Set();
      let before;
      while (true) {
        requireEvidence(++pages <= limits.pages, 'history-limit');
        const page = await request('messages', id, undefined, before);
        requireEvidence(Array.isArray(page.data) && page.data.length <= limits.page, 'invalid-page');
        result.push(...page.data);
        before = page.response.headers.get('x-next-cursor');
        if (before === null) return result;
        requireEvidence(!seen.has(before), 'invalid-cursor');
        seen.add(before);
      }
    },
    close: () => { clearTimeout(timer); signal.removeEventListener('abort', cancel); controller.abort(); },
  };
}
