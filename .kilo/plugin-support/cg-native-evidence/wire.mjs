import { createHash } from 'node:crypto';

/** Internal closed errors. Never construct these from SDK or HTTP error text. */
export class EvidenceError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Reject an unsupported or incomplete condition with a fixed local reason. */
export function requireEvidence(condition, code = 'invalid-native-record') {
  if (!condition) throw new EvidenceError(code);
}

/** Hash acquired bytes or normalized provenance, not an authentication token. */
export function digest(value) { return createHash('sha256').update(value).digest('hex'); }

/** Validate a normalized native ID; e.g. safeID('ses_example', 'ses_'). */
export function safeID(value, prefix = '') {
  requireEvidence(typeof value === 'string' && value.startsWith(prefix) &&
    /^[A-Za-z0-9_-]{1,128}$/.test(value), 'invalid-native-id');
  return value;
}

/**
 * Parse native JSON once. Share budget.remaining across an acquisition; check is
 * its cooperative deadline callback. maxRootItems bounds message pages BEFORE
 * allocating item 51. Keys and values consume nodes before allocation, not bytes
 * or an exact heap estimate. Example: parseWire(text, { budget, maxRootItems: 50 }).
 */
export function parseWire(text, { budget = { remaining: 100000, check: () => {} }, maxRootItems } = {}) {
  let offset = 0;
  let visited = 0;
  const take = () => {
    if ((visited++ & 63) === 0) budget.check();
    requireEvidence(Number.isSafeInteger(budget.remaining) && budget.remaining > 0, 'node-limit');
    budget.remaining--;
  };
  const space = () => {
    while (/[\t\r\n ]/.test(text[offset] ?? '\0')) {
      if ((offset & 4095) === 0) budget.check();
      offset++;
    }
  };
  const fail = () => { throw new EvidenceError('invalid-json'); };
  const string = () => {
    const match = /^"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"/.exec(text.slice(offset));
    if (!match) return fail();
    offset += match[0].length;
    return JSON.parse(match[0]);
  };
  const value = (depth) => {
    if (depth > 64) return fail();
    space();
    const char = text[offset];
    if (depth === 0 && maxRootItems !== undefined) requireEvidence(char === '[', 'invalid-page');
    take();
    if (char === '"') return string();
    if (char === '{' || char === '[') {
      const object = char === '{';
      const close = object ? '}' : ']';
      const result = object ? Object.create(null) : [];
      offset++; space();
      if (text[offset] === close) { offset++; return result; }
      while (offset < text.length) {
        space();
        let key;
        if (object) {
          take();
          key = string(); space();
          if (Object.hasOwn(result, key) || text[offset++] !== ':') return fail();
        } else if (depth === 0 && maxRootItems !== undefined) {
          requireEvidence(result.length < maxRootItems, 'invalid-page');
        }
        const item = value(depth + 1);
        if (object) result[key] = item; else result.push(item);
        space();
        const next = text[offset++];
        if (next === close) return result;
        if (next !== ',') return fail();
      }
      return fail();
    }
    const match = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(offset));
    if (!match) return fail();
    offset += match[0].length;
    const item = JSON.parse(match[0]);
    if (typeof item === 'number' && !Number.isFinite(item)) return fail();
    return item;
  };
  try {
    const result = value(0); space();
    requireEvidence(offset === text.length && result !== null && typeof result === 'object', 'invalid-json');
    budget.check();
    return result;
  } catch (error) { throw error instanceof EvidenceError ? error : new EvidenceError('invalid-json'); }
}
