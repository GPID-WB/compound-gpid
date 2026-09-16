import { EvidenceError, requireEvidence, safeID, digest } from './wire.mjs';
import { createReader } from './transport.mjs';
import { records, samePath } from './records.mjs';

/**
 * Observe trusted context self identity, or return one owned descendant path.
 * childID selects the returned path, not the read scope: the whole bounded caller
 * Task subtree and relevant ancestor histories are scanned, so incomplete siblings
 * can block. Permission waiting precedes the cooperative acquisition deadline.
 * Returns a bounded record with qualification unverified, never bootstrap admission.
 */
export async function acquire(input, context, args, observer = false) {
  let reader;
  try {
    requireEvidence(args && typeof args === 'object' && !Array.isArray(args) &&
      (observer ? Object.keys(args).length === 1 && Object.hasOwn(args, 'childID') :
        Object.keys(args).length === 0), 'invalid-arguments');
    if (observer) {
      try { safeID(args.childID, 'ses_'); } catch { throw new EvidenceError('invalid-arguments'); }
    }
    requireEvidence(context && typeof context.ask === 'function' && context.abort instanceof AbortSignal &&
      samePath(context.directory, input.directory) && samePath(context.worktree, input.worktree) &&
      typeof input.project?.id === 'string', 'native-context-unavailable');
    safeID(context.sessionID, 'ses_'); safeID(context.messageID, 'msg_'); safeID(context.agent);
    requireEvidence(!context.abort.aborted, 'cancelled');
    try {
      await context.ask({ permission: observer ? 'cg_native_evidence' : 'cg_native_identity',
        patterns: [observer ? args.childID : 'self'], always: [], metadata: {} });
    } catch { throw new EvidenceError('permission-denied'); }
    reader = createReader(input, context.abort);
    const store = records(reader, input);
    const own = await store.get(context.sessionID);
    const self = await store.current(context);
    const ancestry = [];
    const ancestorIDs = new Set([own.id]);
    let cursor = own;
    while (cursor.parentID) {
      requireEvidence(ancestry.length < reader.limits.depth, 'depth-limit');
      requireEvidence(!ancestorIDs.has(cursor.parentID), 'ambiguous-history');
      ancestorIDs.add(cursor.parentID);
      const ancestor = await store.get(cursor.parentID);
      const matches = (await store.edges(cursor.parentID)).filter((edge) => edge.childID === cursor.id);
      requireEvidence(matches.length === 1, 'parent-join-unverified');
      const edge = matches[0];
      await store.join(edge);
      if (cursor.id === self.sessionID) requireEvidence(edge.target === self.agent, 'target-mismatch');
      ancestry.push(edge);
      cursor = ancestor;
    }
    const scopeHash = digest(JSON.stringify([input.project.id, input.directory, input.worktree]));
    let output = { schemaVersion: 1, kind: 'native-identity', status: 'observed', qualification: 'unverified',
      reason: null, self, scopeHash, parent: ancestry[0] ?? null,
      ancestors: ancestry.slice(1), provenance: reader.provenance };
    if (observer) {
      requireEvidence(args.childID !== self.sessionID, 'not-owned-target');
      const queue = [{ id: self.sessionID, path: [] }];
      const seen = new Set(ancestorIDs);
      let targetPath;
      while (queue.length) {
        const next = queue.shift();
        for (const edge of await store.edges(next.id)) {
          requireEvidence(ancestry.length + next.path.length < reader.limits.depth, 'depth-limit');
          requireEvidence(!seen.has(edge.childID), 'ambiguous-history'); seen.add(edge.childID);
          await store.join(edge);
          const descendants = [...next.path, edge];
          if (edge.childID === args.childID) targetPath = descendants;
          queue.push({ id: edge.childID, path: descendants });
        }
      }
      requireEvidence(targetPath !== undefined, 'not-owned-target');
      output = { schemaVersion: 1, kind: 'native-evidence', status: 'observed', qualification: 'unverified',
        reason: null, self, scopeHash, edges: targetPath, provenance: reader.provenance };
    }
    reader.check();
    requireEvidence(Buffer.byteLength(JSON.stringify(output)) <= (observer ? 8192 : 4096), 'evidence-too-large');
    return output;
  } catch (error) {
    return { schemaVersion: 1, status: 'blocked', qualification: 'unverified',
      reason: error instanceof EvidenceError ? error.code : 'native-evidence-unavailable' };
  } finally { reader?.close(); }
}

/** Define only passive tools. No hooks, model/session creation or runtime writes. */
export function passiveTools(input, tool) {
  return { tool: {
    cg_native_identity: tool({ description: 'Read trusted current native identity. Evidence only; not bootstrap qualification.',
      args: {}, execute: async (args, context) => JSON.stringify(await acquire(input, context, args, false)) }),
    cg_native_evidence: tool({ description: 'Return one owned descendant path after scanning the whole bounded caller Task subtree. Incomplete siblings can block. Never project-wide lookup or qualification.',
      args: { childID: tool.schema.string().regex(/^ses_[A-Za-z0-9_-]{1,124}$/) },
      execute: async (args, context) => JSON.stringify(await acquire(input, context, args, true)) }),
  } };
}
