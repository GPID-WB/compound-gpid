/* Shared, dependency-free search rules. Also loaded by the Node regression tests. */
(function (root) {
  function slugify(value) {
    return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
      .replace(/[^a-z0-9\s-]/g, "").replace(/[\s-]+/g, "-").replace(/(^-|-$)/g, "");
  }
  function plainText(value) {
    return value.replace(/<!--[^]*?-->/g, "").replace(/[#*`>|\[\]()]/g, " ").replace(/\s+/g, " ").trim();
  }
  /** Split Markdown into searchable sections with the same anchors as the reader. */
  function records(page, markdown) {
    const output = [];
    const counts = new Map();
    let current = { ...page, heading: "", section: "", text: "" };
    let fenced = false;
    const source = markdown.replace(/^\uFEFF/, "").replace(/^---[^]*?---\s*/, "").replace(/<!--[^]*?-->/g, "");
    for (const line of source.split("\n")) {
      if (line.startsWith("```")) { fenced = !fenced; continue; }
      const heading = !fenced && line.match(/^(#{1,6})\s+(.+)$/);
      if (heading) {
        const base = slugify(heading[2]);
        const count = counts.get(base) || 0;
        counts.set(base, count + 1);
        if (heading[1].length > 1) {
          output.push(current);
          current = { ...page, heading: plainText(heading[2]), section: count ? `${base}-${count}` : base, text: "" };
        }
      }
      current.text += ` ${plainText(line)}`;
    }
    output.push(current);
    return output;
  }
  /** Require every query term and rank exact titles/commands ahead of body mentions. */
  function rank(entries, query) {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    const best = new Map();
    for (const entry of entries) {
      const title = entry.title.toLowerCase();
      const heading = entry.heading.toLowerCase();
      const description = entry.description.toLowerCase();
      const body = entry.text.toLowerCase();
      if (!terms.every(term => `${title} ${heading} ${description} ${body}`.includes(term))) continue;
      const score = terms.reduce((total, term) => total + (title.includes(term) ? 35 : 0)
        + (heading.includes(term) ? 25 : 0) + (description.includes(term) ? 8 : 0) + (body.includes(term) ? 1 : 0), 0)
        + (title.replace(/`/g, "") === query.toLowerCase().trim() ? 100 : 0);
      const result = { ...entry, score };
      if (!best.has(entry.id) || best.get(entry.id).score < score) best.set(entry.id, result);
    }
    return [...best.values()].sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  }
  const api = { slugify, records, rank };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DocsSearch = api;
})(typeof globalThis === "undefined" ? this : globalThis);
