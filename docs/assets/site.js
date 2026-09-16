const home = document.querySelector("[data-home]");
const documentView = document.querySelector("[data-document]");
const navigation = document.querySelector("[data-navigation]");
const searchDialog = document.querySelector("[data-search-dialog]");
const searchInput = document.querySelector("[data-search-input]");
const searchResults = document.querySelector("[data-search-results]");
let pages = [];
let pageMap = new Map();
let fileMap = new Map();
let activeResult = -1;
let searchIndex;
let activePage = "";
let navigationRequest = 0;
let activeDocument;
let sectionClick = false;
let lastDocumentRoute = "#home";

function getRoute() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  return { page: params.get("page"), section: params.get("section") };
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function normalizePath(path) {
  const output = [];
  path.split("/").forEach((part) => {
    if (!part || part === ".") return;
    if (part === "..") output.pop(); else output.push(part);
  });
  return output.join("/");
}

function resolveDocLink(href) {
  if (/^(https?:|mailto:)/i.test(href)) {
    return { href, external: true };
  }
  if (href.startsWith("#")) {
    return activePage
      ? { href: `#page=${activePage}&section=${encodeURIComponent(href.slice(1))}` }
      : { href: "#home" };
  }
  const [path, fragment] = href.split("#", 2);
  if (/(?:^|\/)README\.md$/i.test(path)) return { href: "#home" };
  const activeFile = pageMap.get(activePage)?.file || "";
  const base = activeFile.includes("/") ? activeFile.slice(0, activeFile.lastIndexOf("/") + 1) : "";
  const target = normalizePath(`${base}${path}`);
  const page = fileMap.get(target);
  if (page) {
    const section = fragment ? `&section=${encodeURIComponent(fragment)}` : "";
    return { href: `#page=${page.id}${section}` };
  }
  return null;
}

function inlineMarkdown(value) {
  let html = escapeHtml(value);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]+&quot;)?\)/g, (_, label, href) => {
    const resolved = resolveDocLink(href.replace(/&amp;/g, "&"));
    if (!resolved) return `<span class="unresolved-link">${label}</span>`;
    const external = resolved.external ? ' target="_blank" rel="noreferrer"' : "";
    return `<a href="${escapeHtml(resolved.href)}"${external}>${label}</a>`;
  });
  return html;
}

function renderTable(lines) {
  const cells = (line) => {
    const input = line.trim().replace(/^\||\|$/g, "");
    const output = [];
    let cell = "";
    let inCode = false;
    for (let index = 0; index < input.length; index += 1) {
      const character = input[index];
      if (character === "\\" && input[index + 1] === "|") { cell += "|"; index += 1; continue; }
      if (character === "`") inCode = !inCode;
      if (character === "|" && !inCode) { output.push(inlineMarkdown(cell.trim())); cell = ""; continue; }
      cell += character;
    }
    output.push(inlineMarkdown(cell.trim()));
    return output;
  };
  const header = cells(lines[0]);
  const rows = lines.slice(2).map(cells);
  return `<div class="table-wrap" role="region" aria-label="Scrollable table" tabindex="0"><table><thead><tr>${header.map((cell) => `<th scope="col">${cell}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

// The same block tree allocates every H1-H6 ID for rendering and link validation.
function renderBlocks(blocks) {
  return blocks.map((block) => {
    if (block.type === "heading") return `<h${block.level} id="${escapeHtml(block.id)}">${inlineMarkdown(block.text)}</h${block.level}>`;
    if (block.type === "code") return `<pre><button class="copy-code" type="button" aria-label="Copy code">Copy</button><code class="language-${escapeHtml(block.language)}">${escapeHtml(block.text)}</code></pre>`;
    if (block.type === "table") return renderTable(block.lines);
    if (block.type === "hr") return "<hr>";
    if (block.type === "quote") {
      const marker = /^\[!(NOTE|WARNING|TECHNICAL|RESEARCH|SHARED)\](?:\s|$)/.exec(block.children[0]?.text || "");
      if (!marker) return `<blockquote>${renderBlocks(block.children)}</blockquote>`;
      const labels = { NOTE: "Note", WARNING: "Warning", TECHNICAL: "Technical (CG)", RESEARCH: "Research (CR)", SHARED: "Shared" };
      const children = block.children.map((child, index) => index ? child : { ...child, text: child.text.slice(marker[0].length) });
      return `<blockquote class="callout callout-${marker[1].toLowerCase()}"><strong>${labels[marker[1]]}</strong>${renderBlocks(children)}</blockquote>`;
    }
    if (block.type === "list") {
      const tag = block.ordered ? "ol" : "ul";
      return `<${tag}>${block.items.map((item) => {
        const prefix = item.checked === null ? "" : `<span class="task-box" aria-hidden="true">${item.checked ? "&#10003;" : ""}</span>`;
        return `<li>${prefix}${renderBlocks(item.children)}</li>`;
      }).join("")}</${tag}>`;
    }
    return `<p>${inlineMarkdown(block.text)}</p>`;
  }).join("\n");
}

function markdownToHtml(markdown) { return renderBlocks(DocsContract.parseDocument(markdown).blocks); }

async function loadManifest() {
  const response = await fetch("navigation.json");
  if (!response.ok) throw new Error("Could not load documentation navigation.");
  const manifest = await response.json();
  pages = DocsContract.validateManifest(manifest);
  pageMap = new Map(pages.map((page) => [page.id, page]));
  fileMap = new Map(pages.map((page) => [normalizePath(page.file), page]));
  DocsReading.buildNavigation(manifest.groups);
}

async function renderRoute() {
  const raw = getRoute();
  if (location.hash === "#content") {
    history.replaceState(null, "", lastDocumentRoute);
    document.querySelector("#content").focus({ preventScroll: true }); return;
  }
  const { page, section } = DocsContract.resolveRoute(pages, raw.page, raw.section);
  lastDocumentRoute = location.hash || "#home";
  const request = ++navigationRequest;
  DocsReading.updateNavigation(page, pages);
  const focusSection = sectionClick; sectionClick = false;
  if (page && activePage === page && activeDocument) {
    DocsReading.move(section, activeDocument, pageMap.get(page), focusSection); return;
  }
  activeDocument = null;
  DocsReading.clear();
  document.querySelector("[data-reading]").hidden = !page;
  if (!page) {
    activePage = "";
    home.hidden = false;
    documentView.hidden = true;
    document.title = "Compound GPID | Documentation";
    home.scrollIntoView({ behavior: "instant", block: "start" });
    if (!focusSection) document.querySelector("#content").focus({ preventScroll: true });
    return;
  }
  home.hidden = true;
  documentView.hidden = false;
  if (!pageMap.has(page)) {
    activePage = "";
    document.title = "Page not found | Compound GPID";
    documentView.innerHTML = '<h1>Page not found</h1><p>The requested documentation route is not in the public navigation. Return to the <a href="#home">documentation homepage</a> or use search.</p>';
    return;
  }
  documentView.innerHTML = '<p class="loading" role="status">Loading documentation...</p>';
  const config = pageMap.get(page);
  activePage = page;
  document.title = `${config.title} | Compound GPID`;
  try {
    const response = await fetch(config.file);
    if (!response.ok) throw new Error(`Could not load ${config.file}`);
    const markdown = await response.text();
    if (request !== navigationRequest) return;
    const parsed = DocsContract.parseDocument(markdown); activeDocument = parsed;
    documentView.innerHTML = renderBlocks(parsed.blocks);
    DocsReading.mount(config, pages);
    documentView.querySelectorAll(".copy-code").forEach((button) => button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.nextElementSibling.textContent);
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = "Copy"; }, 1300);
    }));
    DocsReading.move(section, parsed, config, focusSection);
    if (!focusSection) document.querySelector("#content").focus({ preventScroll: true });
  } catch (error) {
    if (request !== navigationRequest) return;
    activeDocument = null; DocsReading.clear();
    documentView.innerHTML = `<h1>Page unavailable</h1><p class="error-message">This page could not be loaded. <a href="${escapeHtml(config.file)}">Open the canonical Markdown file</a>.</p>`;
  }
}

async function buildSearchIndex() {
  if (searchIndex) return searchIndex;
  searchIndex = Promise.all(pages.filter(DocsContract.searchable).map(async (page) => {
    try {
      const response = await fetch(page.file);
      const text = response.ok ? await response.text() : "";
      return { ...page, text: text.replace(/[#*`>|\[\]()]/g, " ").replace(/\s+/g, " ") };
    } catch { return { ...page, text: "" }; }
  }));
  return searchIndex;
}

async function search(query) {
  const term = query.trim().toLowerCase();
  const request = query;
  activeResult = -1;
  if (!term) {
    searchResults.innerHTML = '<p class="search-hint">Try <code>install</code>, <code>survey</code>, <code>review</code>, or <code>cg-update</code>.</p>';
    return;
  }
  searchResults.innerHTML = '<p class="search-hint" role="status">Searching documentation...</p>';
  const index = await buildSearchIndex();
  if (searchInput.value !== request) return;
  const results = index.filter((entry) => `${entry.title} ${entry.description} ${entry.text}`.toLowerCase().includes(term)).slice(0, 10);
  searchResults.innerHTML = results.length ? results.map((entry) => {
    const at = entry.text.toLowerCase().indexOf(term);
    const excerpt = at >= 0 ? entry.text.slice(Math.max(0, at - 60), at + term.length + 110) : entry.description;
    return `<a class="search-result" href="#page=${entry.id}"><small>${escapeHtml(entry.group)}</small>${DocsReading.badge(entry.ownerModule).outerHTML}<strong>${escapeHtml(entry.title)}</strong><p>${escapeHtml(excerpt)}...</p></a>`;
  }).join("") : '<p class="search-hint" role="status">No matching documentation. Try a command name or a shorter phrase.</p>';
}

function openSearch() {
  if (!searchDialog.open) searchDialog.showModal();
  setTimeout(() => searchInput.focus(), 0);
}

function closeSearchOnRoute() { if (searchDialog.open) searchDialog.close(); }

document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", openSearch));
DocsReading.init();
document.addEventListener("click", event => {
  const link = event.target.closest("[data-toc] a, .heading-permalink");
  if (link) sectionClick = true;
});
searchInput.addEventListener("input", (event) => search(event.target.value));
searchResults.addEventListener("click", closeSearchOnRoute);
document.querySelector("[data-close-search]").addEventListener("click", () => searchDialog.close());
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openSearch(); }
  if (!searchDialog.open || !["ArrowDown", "ArrowUp", "Enter"].includes(event.key)) return;
  const results = [...searchResults.querySelectorAll(".search-result")];
  if (!results.length) return;
  if (event.key === "Enter" && activeResult >= 0) { results[activeResult].click(); return; }
  event.preventDefault();
  activeResult = event.key === "ArrowDown" ? (activeResult + 1) % results.length : (activeResult - 1 + results.length) % results.length;
  results.forEach((result, index) => result.classList.toggle("selected", index === activeResult));
  results[activeResult].focus();
});

document.querySelector("[data-theme-toggle]").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("compound-theme", next); } catch { /* The DOM retains the selected theme. */ }
});
try {
  const savedTheme = localStorage.getItem("compound-theme");
  if (["light", "dark"].includes(savedTheme)) document.documentElement.dataset.theme = savedTheme;
} catch { /* Reading and theme switching do not require storage. */ }

(async () => {
  try {
    await loadManifest();
    DocsReading.setNavigationOpen(false);
    window.addEventListener("hashchange", renderRoute);
    await renderRoute();
  } catch (error) {
    navigation.textContent = "Navigation could not be loaded.";
    DocsReading.clear(); document.querySelector("[data-reading]").hidden = false;
    home.hidden = true;
    documentView.hidden = false;
    documentView.innerHTML = `<h1>Documentation unavailable</h1><p>${escapeHtml(error.message)}</p>`;
    documentView.focus();
  }
})();
