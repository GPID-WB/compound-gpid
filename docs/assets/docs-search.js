/* Shared search data/ranking contract. Display strings are data, never HTML. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(require("./docs-contract.js"));
  else root.DocsSearch = factory(root.DocsContract);
})(typeof globalThis === "object" ? globalThis : this, function (contract) {
  "use strict";
  const fail = message => { throw new Error(`Documentation search: ${message}`); };
  const keys = (value, names) => value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).length === names.length && names.every(name => Object.hasOwn(value, name));
  const normalize = value => value.normalize("NFC").toLowerCase().replace(/\s+/g, " ").trim();
  // Keep the leading slash: chat prompts and same-name shell commands are distinct.
  const tokens = value => normalize(value).match(/\/?[\p{L}\p{N}\p{M}_]+(?:-[\p{L}\p{N}\p{M}_]+)*/gu) || [];

  /** Validate a complete projection against navigation before caching it; returns the index.
   * Example: validateIndex(JSON.parse(responseText), manifest).
   */
  function validateIndex(index, manifest) {
    if (!keys(index, ["schemaVersion", "headingContract", "entries"])
      || index.schemaVersion !== "compound-gpid-docs-search-v1" || index.headingContract !== contract.headingContract
      || !Array.isArray(index.entries) || index.entries.length > 10000) fail("invalid schema or heading contract");
    const pages = new Map(contract.validateManifest(manifest).filter(contract.searchable).map(page => [page.id, page]));
    const seen = new Set(), roots = new Set();
    for (const entry of index.entries) {
      if (!keys(entry, ["page", "section", "title", "heading", "text", "suite", "kind"])) fail("invalid entry fields");
      const page = pages.get(entry.page);
      if (!page || entry.title !== page.title || !["cg", "cr", "shared"].includes(entry.suite)
        || ![entry.heading, entry.text].every(value => typeof value === "string" && value.length <= 250000)) fail("invalid entry data");
      if (entry.section === null) {
        if (entry.kind !== "page" || entry.heading !== "") fail("invalid page entry");
        roots.add(entry.page);
      } else if (typeof entry.section !== "string" || !/^[\p{L}\p{N}][\p{L}\p{N}\p{M}-]*$/u.test(entry.section)
        || entry.kind !== "section" || !entry.heading.trim()) fail("invalid section entry");
      const id = `${entry.page}#${entry.section || ""}`;
      if (seen.has(id)) fail("duplicate entry");
      seen.add(id);
    }
    if (roots.size !== pages.size) fail("incomplete page coverage");
    return index;
  }

  /** Rank a validated index; exact headings/titles win, with at most two hits per page.
   * Example: rank(index, '/cg-plan') returns entries with bounded plain-text snippets.
   */
  function rank(index, query) {
    if (typeof query !== "string" || query.length > 1024) return [];
    const terms = [...new Set(tokens(query))], phrase = normalize(query);
    if (!terms.length) return [];
    const scored = [];
    index.entries.forEach((entry, position) => {
      const title = normalize(entry.title), heading = normalize(entry.heading), body = normalize(entry.text);
      const titleTokens = tokens(title), headingTokens = tokens(heading), bodyTokens = tokens(body);
      const all = new Set([...titleTokens, ...headingTokens, ...bodyTokens]);
      if (!terms.every(term => all.has(term))) return;
      const score = heading === phrase ? 100 : title === phrase ? (entry.section === null ? 95 : 90)
        : terms.every(term => headingTokens.includes(term)) ? 80
        : terms.every(term => titleTokens.includes(term)) ? 70 : 10;
      scored.push({ entry, score, position });
    });
    scored.sort((a, b) => b.score - a.score || a.position - b.position);
    const count = new Map(), duplicates = new Set(), results = [];
    for (const { entry } of scored) {
      const signature = normalize(`${entry.heading || entry.title}\n${entry.text}`);
      if ((count.get(entry.page) || 0) >= 2 || duplicates.has(signature)) continue;
      count.set(entry.page, (count.get(entry.page) || 0) + 1); duplicates.add(signature);
      const body = normalize(entry.text), at = Math.max(0, body.indexOf(terms[0]) - 50);
      results.push({ ...entry, snippet: entry.text.slice(at, at + 180) });
      if (results.length === 12) break;
    }
    return results;
  }

  return { validateIndex, rank };
});
