/* Shared browser/Node Markdown and navigation contract. No DOM or filesystem access. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DocsContract = factory();
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";
  const headingContract = "compound-gpid-headings-v2";
  const sectionPattern = /^[\p{L}\p{N}][\p{L}\p{N}\p{M}-]*$/u;

  /** Convert heading Markdown to a stable Unicode slug, e.g. `slugify("A/B") === "a-b"`. */
  function slugify(text) {
    return text.normalize("NFC").toLowerCase().replace(/<[^>]*>/g, "")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/[`*_]/g, "")
      .replace(/[^\p{L}\p{N}\p{M}]+/gu, "-").replace(/^-|-$/g, "") || "section";
  }

  /** Exact shipped v1 runtime and validator rules; not used to allocate new IDs. */
  function legacySlugs(text) {
    const value = text.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "");
    return [value.replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
      value.replace(/[^a-z0-9\s-]/g, "").replace(/[\s-]+/g, "-").replace(/(^-|-$)/g, "")];
  }

  const listLine = line => {
    const match = /^(\s*)([-*+]|\d+\.)\s+(.+)$/.exec(line);
    return match && { indent: match[1].replace(/\t/g, "    ").length, ordered: /\d+\./.test(match[2]), text: match[3] };
  };
  const fenceLine = line => /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);

  /** Parse the supported Markdown blocks once for rendering, TOC, validation and search. */
  function parseDocument(markdown) {
    const used = new Set(), headings = [];
    const input = markdown.replace(/^\uFEFF/, "").replace(/\r\n?/g, "\n")
      .replace(/^---\n[\s\S]*?\n---(?:\n|$)/, value => value.replace(/[^\n]/g, ""));
    function parse(lines, offset = 0) {
      const blocks = [];
      let index = 0;
      while (index < lines.length) {
        const line = lines[index];
        if (!line.trim()) { index += 1; continue; }
        if (line.trim().startsWith("<!--")) {
          while (index < lines.length && !lines[index].includes("-->")) index += 1;
          index += 1; continue;
        }
        const fence = fenceLine(line);
        if (fence) {
          const code = [];
          const close = new RegExp(`^ {0,3}${fence[1][0]}{${fence[1].length},}\\s*$`);
          index += 1;
          while (index < lines.length && !close.test(lines[index])) code.push(lines[index++]);
          index += 1;
          blocks.push({ type: "code", language: fence[2].trim(), text: code.join("\n") }); continue;
        }
        if (/^\|/.test(line) && /^\|?\s*:?-{3,}/.test(lines[index + 1] || "")) {
          const table = [line]; index += 1;
          while (index < lines.length && /^\|/.test(lines[index])) table.push(lines[index++]);
          blocks.push({ type: "table", lines: table }); continue;
        }
        const heading = /^ {0,3}(#{1,6})\s+(.+)$/.exec(line);
        if (heading) {
          const text = heading[2].replace(/\s+#+\s*$/, "").trim();
          const base = slugify(text);
          let id = base, suffix = 0;
          while (used.has(id)) id = `${base}-${++suffix}`;
          used.add(id);
          const row = { type: "heading", level: heading[1].length, text, id, line: offset + index, legacy: legacySlugs(heading[2]) };
          headings.push(row); blocks.push(row); index += 1; continue;
        }
        if (/^([-*_])\1\1+\s*$/.test(line)) { blocks.push({ type: "hr" }); index += 1; continue; }
        if (line.startsWith(">")) {
          const quote = [], start = index;
          while (index < lines.length && lines[index].startsWith(">")) quote.push(lines[index++].replace(/^>\s?/, ""));
          blocks.push({ type: "quote", children: parse(quote, offset + start) }); continue;
        }
        const first = listLine(line);
        if (first) {
          const items = [];
          while (index < lines.length) {
            const item = listLine(lines[index]);
            if (!item || item.indent !== first.indent || item.ordered !== first.ordered) break;
            const start = index, body = [item.text]; index += 1;
            while (index < lines.length) {
              const next = listLine(lines[index]);
              if (next && next.indent <= first.indent) break;
              if (!lines[index].trim()) {
                const after = listLine(lines[index + 1] || "");
                if (after && after.indent === first.indent && after.ordered === first.ordered) index += 1;
                break;
              }
              const strip = Math.min(lines[index].match(/^\s*/)[0].length, first.indent + 3);
              body.push(lines[index++].slice(strip));
            }
            const checkbox = /^\[([ xX])\]\s+(.+)$/.exec(body[0]);
            if (checkbox) body[0] = checkbox[2];
            items.push({ checked: checkbox ? Boolean(checkbox[1].trim()) : null, children: parse(body, offset + start) });
          }
          blocks.push({ type: "list", ordered: first.ordered, items }); continue;
        }
        const paragraph = [line]; index += 1;
        while (index < lines.length && lines[index].trim() && !fenceLine(lines[index])
          && !/^ {0,3}(#{1,6}\s|\||>|[-*_]{3,}\s*$|<!--)/.test(lines[index]) && !listLine(lines[index])) paragraph.push(lines[index++]);
        blocks.push({ type: "paragraph", text: paragraph.join(" ") });
      }
      return blocks;
    }
    const blocks = parse(input.split("\n"));
    return { blocks, headings };
  }

  /** Return ordered heading records; e.g. extractHeadings("# Intro")[0].id is "intro". */
  function extractHeadings(markdown) { return parseDocument(markdown).headings; }

  /** Collect unique legacy aliases. Collisions need an explicit per-page sectionAliases record. */
  function headingAliases(headings) {
    const targets = new Map();
    for (const heading of headings) for (const alias of [heading.id, ...heading.legacy]) {
      if (!alias) continue;
      if (!targets.has(alias)) targets.set(alias, new Set());
      targets.get(alias).add(heading.id);
    }
    const aliases = Object.create(null), ambiguous = [];
    for (const [alias, ids] of targets) {
      if (ids.size === 1) aliases[alias] = [...ids][0]; else ambiguous.push(alias);
    }
    return { aliases, ambiguous };
  }

  /** Resolve a fragment without guessing ambiguous old IDs. Return status and, if resolved, id. */
  function resolveSection(headings, section, overrides = {}) {
    if (Object.hasOwn(overrides, section)) return headings.some(h => h.id === overrides[section])
      ? { status: "resolved", id: overrides[section] } : { status: "missing" };
    const { aliases, ambiguous } = headingAliases(headings);
    if (ambiguous.includes(section)) return { status: "ambiguous" };
    return Object.hasOwn(aliases, section) ? { status: "resolved", id: aliases[section] } : { status: "missing" };
  }

  const sidebarVisible = page => page.sidebar !== false;
  const searchable = page => !page.redirect;
  const safePath = value => typeof value === "string" && /^[a-z0-9][a-z0-9./-]*\.md$/.test(value)
    && value.split("/").every(part => part && part !== "." && part !== "..");
  const record = value => value && typeof value === "object" && !Array.isArray(value);
  const section = value => typeof value === "string" && sectionPattern.test(value);
  const mapping = value => record(value) && Object.entries(value).every(([old, target]) => section(old) && section(target));

  /** Validate registration independently of sidebar visibility. Optional headings validate all destinations. */
  function validateManifest(manifest, headings = null) {
    const fail = message => { throw new Error(`Documentation navigation: ${message}`); };
    if (!record(manifest) || manifest.schemaVersion !== "compound-gpid-docs-navigation-v1" || !Array.isArray(manifest.groups)) fail("invalid schema");
    const pages = [], ids = new Set(), files = new Set();
    for (const group of manifest.groups) {
      if (!record(group) || typeof group.title !== "string" || !group.title.trim() || !Array.isArray(group.pages)) fail("invalid group");
      for (const page of group.pages) {
        if (!record(page) || typeof page.id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(page.id) || page.id === "home") fail("unsafe or reserved page ID");
        if (ids.has(page.id)) fail(`duplicate ID ${page.id}`);
        if (!safePath(page.file) || files.has(page.file)) fail(`unsafe or duplicate file ${page.file}`);
        if (![page.title, page.description].every(value => typeof value === "string" && value.trim())) fail(`incomplete metadata ${page.id}`);
        if (Object.hasOwn(page, "sidebar") && typeof page.sidebar !== "boolean") fail(`invalid sidebar ${page.id}`);
        if (Object.hasOwn(page, "sectionAliases") && !mapping(page.sectionAliases)) fail(`invalid aliases ${page.id}`);
        if (page.redirect !== undefined && (!record(page.redirect) || typeof page.redirect.page !== "string"
          || !mapping(page.redirect.sections) || (page.redirect.section !== undefined && !section(page.redirect.section))
          || Object.keys(page.redirect).some(key => !["page", "section", "sections"].includes(key)))) fail(`invalid redirect ${page.id}`);
        pages.push({ ...page, group: group.title }); ids.add(page.id); files.add(page.file);
      }
    }
    const byId = new Map(pages.map(page => [page.id, page]));
    for (const page of pages) {
      const seen = new Set([page.id]);
      for (let current = page; current.redirect;) {
        const target = byId.get(current.redirect.page);
        if (!target) fail(`missing redirect target ${current.redirect.page}`);
        if (seen.has(target.id)) fail(`redirect cycle ${page.id}`);
        seen.add(target.id); current = target;
      }
      if (!headings) continue;
      if (!Array.isArray(headings[page.id])) fail(`missing headings ${page.id}`);
      for (const target of Object.values(page.sectionAliases || {})) {
        if (!headings[page.id].some(h => h.id === target)) fail(`missing alias section ${page.id}#${target}`);
      }
      if (page.redirect) {
        const targets = [...Object.keys(page.redirect.sections), null];
        for (const old of targets) {
          if (old && resolveSection(headings[page.id], old, page.sectionAliases).status !== "resolved") fail(`missing or ambiguous old section ${page.id}#${old}`);
          const route = resolveRoute(pages, page.id, old);
          if (route.section && resolveSection(headings[route.page], route.section, byId.get(route.page).sectionAliases).status !== "resolved") fail(`missing or ambiguous redirect section ${route.page}#${route.section}`);
        }
      }
    }
    return pages;
  }

  /** Follow a validated redirect chain. Unmapped sections survive for explicit missing-section handling. */
  function resolveRoute(pages, page, section = null) {
    const byId = new Map(pages.map(entry => [entry.id, entry])), seen = new Set();
    while (byId.get(page)?.redirect) {
      if (seen.has(page)) throw new Error("Documentation redirect cycle");
      seen.add(page);
      const redirect = byId.get(page).redirect;
      section = section ? (Object.hasOwn(redirect.sections, section) ? redirect.sections[section] : section) : (redirect.section || null);
      page = redirect.page;
    }
    return { page, section };
  }

  return { headingContract, slugify, legacySlugs, parseDocument, extractHeadings, headingAliases,
    resolveSection, validateManifest, resolveRoute, sidebarVisible, searchable };
});
