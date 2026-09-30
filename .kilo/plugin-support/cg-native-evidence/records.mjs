import path from 'node:path';
import { requireEvidence, safeID } from './wire.mjs';

/** Compare trusted runtime directory identities without filesystem effects. */
export function samePath(left, right) {
  if (typeof left !== 'string' || typeof right !== 'string' || !path.isAbsolute(left) || !path.isAbsolute(right)) return false;
  const normalize = (value) => process.platform === 'win32' ? path.resolve(value).toLowerCase() : path.resolve(value);
  return normalize(left) === normalize(right);
}

/** Require a normalized agent name and a finite native timestamp. */
function agent(value) { safeID(value); requireEvidence(value.length <= 64); return value; }
function time(value) { requireEvidence(Number.isSafeInteger(value) && value >= 0 && value <= Date.now()); return value; }

/**
 * Bind records to a trusted factory's worktree. reader must be acquisition-local
 * and closed by its caller. Returns cached get/current/history/edges/join methods;
 * all scanned native Task parts share one four-edge budget, including siblings.
 * Example: const store = records(reader, input); await store.current(context).
 */
export function records(reader, input) {
  const sessions = new Map();
  const histories = new Map();
  const snapshots = new Map();
  const inspected = new Set();
  let workspace;
  let scopeSet = false;
  const get = async (id) => {
    if (sessions.has(id)) return sessions.get(id);
    const item = await reader.get(id);
    requireEvidence(item?.id === id && item.projectID === input.project.id && samePath(item.directory, input.directory), 'scope-mismatch');
    safeID(item.id, 'ses_'); time(item.time?.created);
    if (item.parentID !== undefined) safeID(item.parentID, 'ses_');
    if (item.workspaceID !== undefined) safeID(item.workspaceID);
    if (!scopeSet) { workspace = item.workspaceID; scopeSet = true; }
    requireEvidence(item.workspaceID === workspace, 'scope-mismatch');
    sessions.set(id, item);
    return item;
  };
  const message = (item, id) => {
    requireEvidence(item?.info?.sessionID === id && Array.isArray(item.parts));
    safeID(item.info.id, 'msg_');
    requireEvidence(['assistant', 'user'].includes(item.info.role));
    agent(item.info.agent);
    const created = time(item.info.time?.created);
    for (const stamp of Object.values(item.info.time)) requireEvidence(time(stamp) >= sessions.get(id).time.created);
    if (item.info.time.completed !== undefined) requireEvidence(item.info.time.completed >= created);
    if (item.info.parentID !== undefined) safeID(item.info.parentID, 'msg_');
    for (const part of item.parts) {
      safeID(part.id, 'prt_');
      requireEvidence(part.sessionID === id && part.messageID === item.info.id);
    }
    return item;
  };
  const identity = (item) => JSON.stringify([item.info.id, item.info.sessionID, item.info.role,
    item.info.agent, item.info.time.created, item.info.parentID ?? null]);
  const reconcile = (id, items) => {
    const snapshot = snapshots.get(id);
    if (!snapshot) return;
    const matches = items.filter((item) => item.info.id === snapshot.id);
    requireEvidence(matches.length === 1 && identity(matches[0]) === snapshot.identity, 'current-history-mismatch');
  };
  const history = async (id) => {
    if (histories.has(id)) return histories.get(id);
    await get(id);
    const items = await reader.messages(id);
    // Charge distinct inspected dispatches once, before validation and repeated searches.
    for (const item of items) {
      reader.check();
      for (const part of Array.isArray(item?.parts) ? item.parts : []) {
        if (part?.type !== 'tool' || part.tool !== 'task') continue;
        const key = JSON.stringify([id, safeID(item.info?.id, 'msg_'), safeID(part.id, 'prt_')]);
        if (!inspected.has(key)) {
          requireEvidence(inspected.size < reader.limits.edges, 'edge-limit');
          inspected.add(key);
        }
      }
    }
    const ids = new Set();
    const parts = new Set();
    const calls = new Set();
    for (const item of items) {
      message(item, id);
      requireEvidence(!ids.has(item.info.id), 'ambiguous-history'); ids.add(item.info.id);
      for (const part of item.parts) {
        requireEvidence(!parts.has(part.id), 'ambiguous-history'); parts.add(part.id);
        if (part.type === 'tool' && part.tool === 'task') {
          safeID(part.callID);
          requireEvidence(!calls.has(part.callID), 'ambiguous-history'); calls.add(part.callID);
        }
      }
    }
    reconcile(id, items);
    histories.set(id, items);
    return items;
  };
  const edges = async (id) => {
    const items = await history(id);
    const result = [];
    const children = new Set();
    for (const item of items) for (const part of item.parts) {
      if (part.type !== 'tool' || part.tool !== 'task') continue;
      requireEvidence(item.info.role === 'assistant');
      const state = part.state;
      requireEvidence(state && ['running', 'completed', 'error'].includes(state.status), 'incomplete-task');
      const meta = state.metadata;
      requireEvidence(meta?.parentSessionId === id && typeof meta.sessionId === 'string', 'incomplete-task');
      safeID(meta.sessionId, 'ses_');
      requireEvidence(!children.has(meta.sessionId), 'ambiguous-history'); children.add(meta.sessionId);
      requireEvidence(state.input && typeof state.input === 'object' && !Array.isArray(state.input), 'reused-task');
      if (Object.hasOwn(state.input, 'task_id')) {
        requireEvidence(typeof state.input.task_id === 'string' && state.input.task_id === '', 'reused-task');
      }
      const target = agent(state.input.subagent_type);
      for (const value of [state.input.background, meta.background]) requireEvidence(value === undefined || typeof value === 'boolean');
      const user = items.find((candidate) => candidate.info.id === item.info.parentID);
      requireEvidence(user?.info.role === 'user' && user.info.agent === item.info.agent &&
        !user.parts.some((p) => ['agent', 'subtask'].includes(p.type)), 'dispatch-origin-unverified');
      const start = time(state.time?.start);
      const end = state.status === 'running' && state.time?.end === undefined ? null : time(state.time?.end);
      requireEvidence(user.info.time.created <= item.info.time.created && start >= item.info.time.created &&
        (end === null || end >= start));
      result.push({ parentID: id, childID: meta.sessionId, messageID: item.info.id,
        partID: part.id, callID: part.callID, agent: item.info.agent, target,
        state: state.status, start, end, background: state.input.background === true || meta.background === true });
    }
    return result;
  };
  const join = async (edge) => {
    const child = await get(edge.childID);
    requireEvidence(child.parentID === edge.parentID && child.time.created >= edge.start &&
      (edge.end === null || child.time.created <= edge.end), 'child-join-mismatch');
    const items = await history(child.id);
    const users = items.filter((item) => item.info.role === 'user').sort((a, b) => a.info.time.created - b.info.time.created);
    requireEvidence(users.length > 0 && (users.length === 1 || users[0].info.time.created !== users[1].info.time.created),
      'initial-message-ambiguous');
    requireEvidence(users.length > 0 && users[0].info.agent === edge.target &&
      !users[0].parts.some((p) => ['agent', 'subtask'].includes(p.type)), 'target-mismatch');
    return child;
  };
  return { get, history, edges, join,
    current: async (context) => {
      await get(context.sessionID);
      const item = message(await reader.message(context.sessionID, context.messageID), context.sessionID);
      requireEvidence(item.info.id === context.messageID && item.info.role === 'assistant' &&
        item.info.agent === context.agent && item.info.time.completed === undefined, 'current-identity-mismatch');
      snapshots.set(context.sessionID, { id: item.info.id, identity: identity(item) });
      if (histories.has(context.sessionID)) reconcile(context.sessionID, histories.get(context.sessionID));
      return { sessionID: context.sessionID, messageID: context.messageID, agent: agent(context.agent) };
    },
  };
}
