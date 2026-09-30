// Wire fixtures follow the public v7.6.2 SDK request and session contracts.
export const directory = process.platform === 'win32' ? 'E:/native-evidence/worktree' : '/native-evidence/worktree';
export const rootID = 'ses_root';
export const childID = 'ses_child';
export const secret = 'SECRET_SENTINEL_DO_NOT_RETURN';

/** Build a minimal native Task edge and current tool context for offline tests. */
export function fixture() {
  const session = (id, parentID) => ({
    id, parentID, directory, projectID: 'project_test', version: '7.6.2',
    agent: 'mutable-selection-not-authority', time: { created: id === rootID ? 1 : 12, updated: 30 },
  });
  const user = (id, sid, agent) => ({
    info: { id, sessionID: sid, role: 'user', agent, time: { created: sid === rootID ? 10 : 13 } },
    parts: [{ id: `prt_${id}`, sessionID: sid, messageID: id, type: 'text', text: secret }],
  });
  const assistant = (id, sid, agent, parentID) => ({
    info: { id, sessionID: sid, role: 'assistant', agent, parentID, time: { created: sid === rootID ? 11 : 14 } }, parts: [],
  });
  const dispatch = assistant('msg_dispatch', rootID, 'code', 'msg_user');
  dispatch.parts.push({
    id: 'prt_dispatch', callID: 'call_dispatch', messageID: dispatch.info.id,
    sessionID: rootID, type: 'tool', tool: 'task', state: {
      status: 'completed', input: { subagent_type: 'cg-workflow-stage', prompt: secret, background: false },
      metadata: { parentSessionId: rootID, sessionId: childID },
      time: { start: 11, end: 20 }, output: secret,
    },
  });
  const records = {
    [rootID]: { session: session(rootID), messages: [user('msg_user', rootID, 'code'), dispatch,
      assistant('msg_current', rootID, 'code', 'msg_user')] },
    [childID]: { session: session(childID, rootID), messages: [user('msg_childuser', childID, 'cg-workflow-stage'),
      assistant('msg_childcurrent', childID, 'cg-workflow-stage', 'msg_childuser')] },
  };
  const requests = [];
  const nativeFetch = async (request) => {
    requests.push(request);
    const url = new URL(request.url);
    const [, , id, kind, messageID] = url.pathname.split('/');
    const item = records[id];
    if (!item) return new Response(secret, { status: 404 });
    const value = !kind ? item.session : messageID
      ? item.messages.find((row) => row.info.id === messageID) : item.messages;
    return Response.json(value ?? null);
  };
  return { records, dispatch, requests, nativeFetch,
    context: { sessionID: rootID, messageID: 'msg_current', agent: 'code', directory, worktree: directory,
      abort: new AbortController().signal, ask: async () => {} },
  };
}

/** Exercise merged public request options, SDK Request creation and pre-parse fetch. */
export function sdkFixture(fetch, { validator = true, origin = 'http://localhost:4096' } = {}) {
  const request = async (url, options) => {
    const opts = { baseUrl: origin, fetch, method: 'GET', ...options };
    if (validator) await opts.requestValidator?.(opts);
    let path = url.replace('{id}', encodeURIComponent(opts.path.id));
    if (opts.path.messageID) path = path.replace('{messageID}', encodeURIComponent(opts.path.messageID));
    const address = new URL(path, opts.baseUrl);
    for (const [key, value] of Object.entries(opts.query ?? {})) {
      if (value !== undefined) address.searchParams.set(key, String(value));
    }
    const req = new Request(address, { method: opts.method, signal: opts.signal,
      redirect: opts.redirect ?? 'follow', headers: { authorization: secret } });
    const response = await opts.fetch(req);
    // Exactly the relevant SDK ordering: errors otherwise call text() without a cap.
    if (response.ok && opts.parseAs === 'stream') return { data: response.body, response, request: req };
    return response.ok ? { data: await response.json(), response, request: req }
      : { error: await response.text(), response, request: req };
  };
  return { session: {
    get: (options) => request('/session/{id}', options),
    message: (options) => request('/session/{id}/message/{messageID}', options),
    messages: (options) => request('/session/{id}/message', options),
  } };
}

/** Create trusted factory input; no caller argument can select this binding. */
export function inputFor(client) {
  return { client, directory, worktree: directory, project: { id: 'project_test' },
    serverUrl: new URL('http://localhost:4096') };
}

/** Same-millisecond native chain for graph caps, not a settlement qualification. */
export function chain(length) {
  const f = fixture();
  const template = structuredClone(f.records[rootID]);
  const ids = [rootID, childID, ...Array.from({ length: length - 2 }, (_, i) => `ses_extra_${i}`)];
  for (const [index, id] of ids.entries()) {
    const record = structuredClone(template);
    record.session.id = id; record.session.parentID = ids[index - 1]; record.session.time.created = 12;
    for (const row of record.messages) {
      row.info.sessionID = id; row.info.agent = 'code'; row.info.time.created = 12;
      for (const part of row.parts) part.sessionID = id;
    }
    if (index + 1 === length) record.messages[1].parts = [];
    else {
      const state = record.messages[1].parts[0].state;
      state.input.subagent_type = 'code'; state.time.start = 12;
      state.metadata = { parentSessionId: id, sessionId: ids[index + 1] };
    }
    f.records[id] = record;
  }
  return { f, ids };
}
