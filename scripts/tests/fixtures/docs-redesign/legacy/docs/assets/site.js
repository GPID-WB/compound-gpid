const home = document.querySelector("[data-home]");
const documentView = document.querySelector("[data-document]");
const sidebar = document.querySelector(".sidebar");
const navigation = document.querySelector("[data-navigation]");
const menuButton = document.querySelector("[data-menu-toggle]");
const menuClose = document.querySelector("[data-menu-close]");
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

function getRoute() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  return { page: params.get("page"), section: params.get("section") };
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function slugify(value) {
  return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
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

function listLine(line) {
  const match = line.match(/^(\s*)([-*+]|\d+\.)\s+(.+)$/);
  return match && { indent: match[1].replace(/\t/g, "    ").length, ordered: /\d+\./.test(match[2]), text: match[3] };
}

function renderList(lines, start, indent) {
  const first = listLine(lines[start]);
  const tag = first.ordered ? "ol" : "ul";
  const items = [];
  let index = start;
  while (index < lines.length) {
    const item = listLine(lines[index]);
    if (!item || item.indent !== indent || item.ordered !== first.ordered) break;
    const body = [item.text];
    index += 1;
    while (index < lines.length) {
      const next = listLine(lines[index]);
      if (next && next.indent === indent && next.ordered === first.ordered) break;
      if (next && next.indent < indent) break;
      if (!lines[index].trim()) {
        const afterBlank = listLine(lines[index + 1] || "");
        if (afterBlank && afterBlank.indent === indent && afterBlank.ordered === first.ordered) { index += 1; break; }
        break;
      }
      const strip = Math.min(lines[index].match(/^\s*/)[0].length, indent + 3);
      body.push(lines[index].slice(strip));
      index += 1;
    }
    const checkbox = body[0].match(/^\[([ xX])\]\s+(.+)$/);
    if (checkbox) body[0] = checkbox[2];
    const prefix = checkbox ? `<span class="task-box" aria-hidden="true">${checkbox[1].trim() ? "✓" : ""}</span>` : "";
    items.push(`<li>${prefix}${markdownToHtml(body.join("\n"))}</li>`);
  }
  return { html: `<${tag}>${items.join("")}</${tag}>`, index };
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/^\uFEFF/, "").replace(/^---[\s\S]*?---\s*/, "").split("\n");
  const output = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }
    if (line.trim().startsWith("<!--")) {
      while (index < lines.length && !lines[index].includes("-->")) index += 1;
      index += 1;
      continue;
    }
    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) code.push(lines[index++]);
      index += 1;
      output.push(`<pre><button class="copy-code" type="button" aria-label="Copy code">Copy</button><code class="language-${escapeHtml(language)}">${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }
    if (/^\|/.test(line) && /^\|?\s*:?-{3,}/.test(lines[index + 1] || "")) {
      const table = [line];
      index += 1;
      while (index < lines.length && /^\|/.test(lines[index])) table.push(lines[index++]);
      output.push(renderTable(table));
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const text = heading[2];
      output.push(`<h${level} id="${slugify(text)}">${inlineMarkdown(text)}</h${level}>`);
      index += 1;
      continue;
    }
    if (/^([-*_])\1\1+\s*$/.test(line)) { output.push("<hr>"); index += 1; continue; }
    if (line.startsWith(">")) {
      const quote = [];
      while (index < lines.length && lines[index].startsWith(">")) quote.push(lines[index++].replace(/^>\s?/, ""));
      output.push(`<blockquote>${markdownToHtml(quote.join("\n"))}</blockquote>`);
      continue;
    }
    const list = listLine(line);
    if (list) {
      const rendered = renderList(lines, index, list.indent);
      output.push(rendered.html);
      index = rendered.index;
      continue;
    }
    const paragraph = [line];
    index += 1;
    while (index < lines.length && lines[index].trim()
      && !/^(#{1,6}\s|```|\||>|[-*_]{3,}\s*$)/.test(lines[index])
      && !listLine(lines[index])) paragraph.push(lines[index++]);
    output.push(`<p>${inlineMarkdown(paragraph.join(" "))}</p>`);
  }
  return output.join("\n");
}

function buildNavigation(groups) {
  navigation.replaceChildren();
  const appendLink = (parent, id, number, title) => {
    const link = document.createElement("a");
    link.href = id === "home" ? "#home" : `#page=${encodeURIComponent(id)}`;
    link.dataset.route = id;
    const label = document.createElement("span");
    label.textContent = number;
    link.append(label, ` ${title}`);
    parent.append(link);
  };
  appendLink(navigation, "home", "00", "Overview");
  groups.forEach((group, groupIndex) => {
    const section = document.createElement("section");
    section.className = "nav-group";
    const heading = document.createElement("h2");
    heading.id = `nav-group-${groupIndex}`;
    heading.textContent = group.title;
    section.setAttribute("aria-labelledby", heading.id);
    section.append(heading);
    group.pages.forEach((page, pageIndex) => appendLink(section, page.id, `${groupIndex + 1}.${pageIndex + 1}`, page.title));
    navigation.append(section);
  });
}

async function loadManifest() {
  const response = await fetch("navigation.json");
  if (!response.ok) throw new Error("Could not load documentation navigation.");
  const manifest = await response.json();
  if (!Array.isArray(manifest.groups)) throw new Error("Documentation navigation is invalid.");
  for (const group of manifest.groups) {
    if (!group || typeof group.title !== "string" || !Array.isArray(group.pages)) {
      throw new Error("Documentation navigation group is invalid.");
    }
    for (const page of group.pages) {
      if (!page || !/^[a-z0-9-]+$/.test(page.id) || typeof page.title !== "string"
        || typeof page.description !== "string" || typeof page.file !== "string"
        || !/^[a-z0-9][a-z0-9./-]*\.md$/.test(page.file) || page.file.includes("..")) {
        throw new Error("Documentation navigation page is invalid.");
      }
    }
  }
  pages = manifest.groups.flatMap((group) => group.pages.map((page) => ({ ...page, group: group.title })));
  pageMap = new Map(pages.map((page) => [page.id, page]));
  fileMap = new Map(pages.map((page) => [normalizePath(page.file), page]));
  buildNavigation(manifest.groups);
}

function updateNavigation(page) {
  document.querySelectorAll("[data-route]").forEach((link) => {
    const active = link.dataset.route === (page || "home");
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
  });
  setNavigationOpen(false);
}

async function renderRoute() {
  const { page, section } = getRoute();
  const request = ++navigationRequest;
  updateNavigation(page);
  if (!page) {
    activePage = "";
    home.hidden = false;
    documentView.hidden = true;
    document.title = "Compound GPID | Documentation";
    home.scrollIntoView({ behavior: "instant", block: "start" });
    document.querySelector("#content").focus({ preventScroll: true });
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
    documentView.innerHTML = markdownToHtml(markdown);
    documentView.querySelectorAll(".copy-code").forEach((button) => button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.nextElementSibling.textContent);
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = "Copy"; }, 1300);
    }));
    const target = section && document.getElementById(section);
    (target || documentView).scrollIntoView({ behavior: "instant", block: "start" });
    document.querySelector("#content").focus({ preventScroll: true });
  } catch (error) {
    if (request !== navigationRequest) return;
    documentView.innerHTML = `<h1>Page unavailable</h1><p class="error-message">This page could not be loaded. <a href="${escapeHtml(config.file)}">Open the canonical Markdown file</a>.</p>`;
  }
}

async function buildSearchIndex() {
  if (searchIndex) return searchIndex;
  searchIndex = Promise.all(pages.map(async (page) => {
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
    return `<a class="search-result" href="#page=${entry.id}"><small>${escapeHtml(entry.group)}</small><strong>${escapeHtml(entry.title)}</strong><p>${escapeHtml(excerpt)}...</p></a>`;
  }).join("") : '<p class="search-hint" role="status">No matching documentation. Try a command name or a shorter phrase.</p>';
}

function openSearch() {
  if (!searchDialog.open) searchDialog.showModal();
  setTimeout(() => searchInput.focus(), 0);
}

function closeSearchOnRoute() { if (searchDialog.open) searchDialog.close(); }

function setNavigationOpen(opened) {
  const mobile = window.matchMedia("(max-width: 820px)").matches;
  const isOpen = opened && mobile;
  const focusWasInSidebar = sidebar.contains(document.activeElement);
  sidebar.classList.toggle("open", isOpen);
  sidebar.inert = mobile && !isOpen;
  sidebar.setAttribute("aria-hidden", String(mobile && !isOpen));
  menuButton.setAttribute("aria-expanded", String(isOpen));
  menuButton.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
  menuClose.hidden = !isOpen;
  document.querySelector("main").inert = isOpen;
  document.body.classList.toggle("navigation-open", isOpen);
  if (isOpen) sidebar.querySelector("a")?.focus();
  if (mobile && !isOpen && focusWasInSidebar) menuButton.focus();
}

document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", openSearch));
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

menuButton.addEventListener("click", () => setNavigationOpen(!sidebar.classList.contains("open")));
menuClose.addEventListener("click", () => setNavigationOpen(false));
document.querySelector("[data-theme-toggle]").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("compound-theme", next);
});
window.addEventListener("resize", () => setNavigationOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && sidebar.classList.contains("open")) setNavigationOpen(false);
});
const savedTheme = localStorage.getItem("compound-theme");
if (savedTheme) document.documentElement.dataset.theme = savedTheme;

(async () => {
  try {
    await loadManifest();
    setNavigationOpen(false);
    window.addEventListener("hashchange", renderRoute);
    await renderRoute();
  } catch (error) {
    navigation.querySelector(".nav-loading").textContent = "Navigation could not be loaded.";
    home.hidden = true;
    documentView.hidden = false;
    documentView.innerHTML = `<h1>Documentation unavailable</h1><p>${escapeHtml(error.message)}</p>`;
    documentView.focus();
  }
})();
