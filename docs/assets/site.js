const SHELL_BUILD_ID = "__CG_DOCS_SHELL_BUILD_ID__";
const home = document.querySelector("[data-home]");
const documentView = document.querySelector("[data-document]");
const navigation = document.querySelector("[data-navigation]");
let pages = [];
let pageMap = new Map();
let fileMap = new Map();
let activePage = "";
let navigationRequest = 0;
let activeDocument;
let sectionClick = false;
let lastDocumentRoute = "#home";
// Filled only after step 5's shell/content verifier establishes source identity.
let verifiedSource = null;

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
  const source = DocsTools.repositoryUrl(href, activeFile, verifiedSource?.sha);
  return source ? { href: source, external: true } : null;
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
  // Decode one level of authored entities only after Markdown syntax handling.
  // Character references render as text; they cannot introduce HTML elements.
  return html.replace(/&amp;((?:#\d+|#x[0-9a-f]+|lt|gt|amp|quot|apos);)/gi, "&$1");
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
    if (block.type === "code") {
      const copy = DocsTools.copyable(block);
      return `<div class="code-block"><pre>${copy ? '<button class="copy-code" type="button" aria-label="Copy code">Copy</button>' : ""}<code class="language-${escapeHtml(block.language)}">${escapeHtml(block.text)}</code></pre>${copy ? '<p class="copy-status" role="status" aria-live="polite"></p><button class="select-code" type="button" hidden>Select code</button>' : ""}</div>`;
    }
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
  const manifest = JSON.parse(await DocsIdentity.read("navigation.json"));
  pages = DocsContract.validateManifest(manifest);
  pageMap = new Map(pages.map((page) => [page.id, page]));
  fileMap = new Map(pages.map((page) => [normalizePath(page.file), page]));
  DocsReading.buildNavigation(manifest.groups);
  DocsSearch.init(manifest, document.querySelector("[data-build-identity]").textContent);
}

function mountDocument(config, parsed, retainedNodes = null) {
  if (retainedNodes) documentView.replaceChildren(...retainedNodes);
  else documentView.innerHTML = renderBlocks(parsed.blocks);
  DocsReading.mount(config, pages);
  if (!retainedNodes) { DocsTools.mount(documentView); DocsCommands.mount(documentView, config); }
  const sourceLink = document.querySelector("[data-document-source]");
  sourceLink.href = verifiedSource ? DocsTools.repositoryUrl(config.file.split("/").at(-1), config.file, verifiedSource.sha) : config.file;
  sourceLink.textContent = verifiedSource ? "View source at this revision" : "Raw Markdown (unverified build)"; sourceLink.hidden = false;
  const issue = document.querySelector("[data-page-issue]"); issue.hidden = !verifiedSource;
  if (verifiedSource) issue.href = DocsTools.issueUrl(config.id, verifiedSource.channel, verifiedSource.sha);
}

async function renderRoute() {
  const raw = getRoute();
  if (location.hash === "#content") {
    history.replaceState(null, "", lastDocumentRoute);
    document.querySelector("#content").focus({ preventScroll: true }); return;
  }
  const { page, section } = DocsContract.resolveRoute(pages, raw.page, raw.section);
  const retained = { page: activePage, document: activeDocument, nodes: [...documentView.childNodes] };
  lastDocumentRoute = location.hash || "#home";
  const request = ++navigationRequest;
  DocsReading.updateNavigation(page, pages);
  const focusSection = sectionClick; sectionClick = false;
  if (page && activePage === page && activeDocument) {
    DocsReading.move(section, activeDocument, pageMap.get(page), focusSection); return;
  }
  activeDocument = null;
  DocsReading.clear();
  document.querySelector("[data-document-source]").hidden = true;
  document.querySelector("[data-reading]").hidden = !page;
  if (!page) {
    document.querySelector("[data-build-identity]").textContent = DocsIdentity.label();
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
    document.querySelector("[data-build-identity]").textContent = DocsIdentity.label();
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
    const markdown = await DocsIdentity.read(config.file);
    if (request !== navigationRequest) return;
    const parsed = DocsContract.parseDocument(markdown); activeDocument = parsed;
    mountDocument(config, parsed);
    DocsReading.move(section, parsed, config, focusSection);
    if (!focusSection) document.querySelector("#content").focus({ preventScroll: true });
  } catch (error) {
    if (request !== navigationRequest) return;
    if (error.buildChanged && retained.document) {
      activePage = retained.page; activeDocument = retained.document;
      document.title = `${pageMap.get(activePage).title} | Compound GPID`;
      DocsReading.updateNavigation(activePage, pages);
      mountDocument(pageMap.get(activePage), activeDocument, retained.nodes);
      return;
    }
    activeDocument = null; DocsReading.clear();
    documentView.innerHTML = `<h1>Page unavailable</h1><p class="error-message">This page could not be loaded. <a href="${escapeHtml(config.file)}">Open the canonical Markdown file</a>.</p>`;
  }
}

document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", DocsSearch.open));
DocsReading.init();
DocsTools.init();
document.addEventListener("click", event => {
  const link = event.target.closest("[data-toc] a, .heading-permalink");
  if (link) sectionClick = true;
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
    verifiedSource = await DocsIdentity.init(SHELL_BUILD_ID);
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
