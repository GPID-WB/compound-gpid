/* Shared, dependency-free search rules. Also loaded by the Node regression tests. */
(function (root) {
  function slugify(value) {
    return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
      .replace(/[^a-z0-9\s-]/g, "").replace(/[\s-]+/g, "-").replace(/(^-|-$)/g, "");
  }
  /** Allocate and reserve the next unused anchor for a heading. */
  function headingId(value, used) {
    const base = slugify(value);
    let id = base;
    for (let suffix = 1; used.has(id); suffix += 1) id = `${base}-${suffix}`;
    used.add(id);
    return id;
  }
  /** Match an opening fence, or a compatible closing fence when opener is supplied. */
  function codeFence(line, opener = "") {
    const match = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (!match) return null;
    const [, marker, info] = match;
    if (opener ? marker[0] !== opener[0] || marker.length < opener.length || !/^[ \t]*$/.test(info)
      : marker[0] === "`" && info.includes("`")) return null;
    return { marker, info: info.trim() };
  }
  /** Split Markdown, excluding any opening front matter with exact delimiters. */
  function markdownLines(markdown) {
    const lines = markdown.replace(/^\uFEFF/, "").split(/\r?\n/);
    const close = lines[0] === "---" ? lines.indexOf("---", 1) : -1;
    return close === -1 ? lines : lines.slice(close + 1);
  }
  function plainText(value) {
    return value.replace(/[#*`>|\[\]()]/g, " ").replace(/\s+/g, " ").trim();
  }
  /** Split Markdown into searchable sections with the same anchors as the reader. */
  function records(page, markdown) {
    const output = [];
    const used = new Set();
    let current = { ...page, heading: "", section: "", text: "" };
    let opener = "";
    let inComment = false;
    for (const line of markdownLines(markdown)) {
      if (!opener && (inComment || line.trimStart().startsWith("<!--"))) {
        inComment = !line.includes("-->");
        continue;
      }
      const fence = codeFence(line, opener);
      if (fence) { opener = opener ? "" : fence.marker; continue; }
      const text = opener ? line : line.replace(/<!--.*?-->/g, "");
      const heading = !opener && text.match(/^(#{1,6})\s+(.+)$/);
      if (heading) {
        const id = headingId(heading[2], used);
        if (heading[1].length > 1) {
          output.push(current);
          current = { ...page, heading: plainText(heading[2]), section: id, text: "" };
        }
      }
      current.text += ` ${plainText(text)}`;
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
  const api = { slugify, headingId, codeFence, markdownLines, records, rank };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DocsSearch = api;
})(typeof globalThis === "undefined" ? this : globalThis);
