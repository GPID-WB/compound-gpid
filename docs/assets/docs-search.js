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

  let openDialog;

  /** Bind one lazy, channel-local index and keyboard dialog after navigation validation. */
  function init(manifest, channelLabel) {
    const dialog = document.querySelector("[data-search-dialog]"), input = document.querySelector("[data-search-input]");
    const container = document.querySelector("[data-search-results]");
    let pending, request = 0, selected = -1, opener;
    function message(value, role = "status") {
      const node = document.createElement("p"); node.className = "search-hint";
      node.setAttribute("role", role); node.textContent = value; container.replaceChildren(node);
    }
    async function perform(query) {
      const current = ++request; selected = -1;
      if (!query.trim()) { message("Try install, survey, review, or cg-update."); return; }
      message("Searching documentation...");
      try {
        if (!pending) pending = fetch("assets/search-index.json").then(async response => {
          if (!response.ok) throw new Error("Search index unavailable");
          return validateIndex(await response.json(), manifest);
        }).catch(error => { pending = null; throw error; });
        const index = await pending;
        if (current !== request || !dialog.open) return;
        const results = rank(index, query);
        if (!results.length) { message("No matching documentation. Try a command name or a shorter phrase."); return; }
        container.replaceChildren();
        for (const entry of results) {
          const link = document.createElement("a"), meta = document.createElement("small"), badge = document.createElement("span");
          const heading = document.createElement("strong"), snippet = document.createElement("p");
          link.className = "search-result";
          link.href = `#page=${encodeURIComponent(entry.page)}${entry.section ? `&section=${encodeURIComponent(entry.section)}` : ""}`;
          meta.textContent = `${entry.kind === "section" ? `Section in ${entry.title}` : "Page"} | ${channelLabel}`;
          const suite = { cg: ["technical", "Technical (CG)"], cr: ["research", "Research (CR)"], shared: ["shared", "Shared"] }[entry.suite];
          badge.className = `suite-badge suite-${suite[0]}`; badge.textContent = suite[1];
          heading.textContent = entry.heading || entry.title; snippet.textContent = entry.snippet;
          link.append(meta, badge, heading, snippet); container.append(link);
        }
      } catch {
        if (current !== request || !dialog.open) return;
        message("Search unavailable. You can still read documentation or retry.", "alert");
        const retry = document.createElement("button"); retry.type = "button"; retry.className = "search-retry";
        retry.textContent = "Retry search"; retry.addEventListener("click", () => perform(input.value)); container.append(retry);
      }
    }
    openDialog = () => {
      if (!dialog.open) { opener = document.activeElement; dialog.showModal(); perform(input.value); }
      input.focus();
    };
    input.addEventListener("input", () => perform(input.value));
    container.addEventListener("click", event => { if (event.target.closest(".search-result")) dialog.close(); });
    container.addEventListener("focusin", event => {
      const link = event.target.closest(".search-result"); if (!link) return;
      const results = [...container.querySelectorAll(".search-result")]; selected = results.indexOf(link);
      results.forEach((result, index) => result.classList.toggle("selected", index === selected));
    });
    document.querySelector("[data-close-search]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => { request += 1; opener?.focus(); });
    document.addEventListener("keydown", event => {
      if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "k") { event.preventDefault(); openDialog(); }
    });
    dialog.addEventListener("keydown", event => {
      if (!["ArrowDown", "ArrowUp", "Enter"].includes(event.key) || event.target.closest("button")) return;
      const results = [...container.querySelectorAll(".search-result")]; if (!results.length) return;
      if (event.key === "Enter") {
        if (event.target === input && selected >= 0) { event.preventDefault(); results[selected].click(); }
        return;
      }
      event.preventDefault();
      selected = event.key === "ArrowDown" ? (selected + 1) % results.length : (selected - 1 + results.length) % results.length;
      results.forEach((result, index) => result.classList.toggle("selected", index === selected)); results[selected].focus();
    });
    document.querySelector(".search-trigger kbd").textContent = /Mac|iPhone|iPad/.test(navigator.platform) ? "Cmd K" : "Ctrl K";
  }

  /** Open the initialized search dialog without intercepting unmodified typing. */
  function open() { openDialog?.(); }

  return { validateIndex, rank, init, open };
});
