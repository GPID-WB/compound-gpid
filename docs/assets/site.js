const pages = [
  ["installation", "Installation", "installation.md"],
  ["workflow", "Workflow", "workflow.md"],
  ["reference", "Command Reference", "reference.md"],
  ["context-files", "Context Files", "context-files.md"],
  ["model-guide", "Model Guide", "model-guide.md"],
  ["team-brain-schema", "Team Brain", "team-brain-schema.md"],
  ["retrieval-backends", "Retrieval Backends", "retrieval-backends.md"],
  ["snapshot-external-research", "Snapshot & External Research", "snapshot-external-research.md"],
  ["versioning", "Updates & Versions", "versioning.md"],
  ["troubleshooting", "Troubleshooting", "troubleshooting.md"],
  ["manual", "Manual", "manual.md"],
  ["competitive-reviews", "Competitive Reviews", "competitive-reviews.md"]
];

const pageMap = new Map(pages.map(([id, title, file]) => [id, { title, file }]));
const home = document.querySelector("[data-home]");
const documentView = document.querySelector("[data-document]");
const sidebar = document.querySelector(".sidebar");
const menuButton = document.querySelector("[data-menu-toggle]");
const searchDialog = document.querySelector("[data-search-dialog]");
const searchInput = document.querySelector("[data-search-input]");
const searchResults = document.querySelector("[data-search-results]");
let activeResult = -1;
let searchIndex;
let activePage = "";
let navigationRequest = 0;

function getRoute() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  return { page: params.get("page"), section: params.get("section") };
}

function escapeHtml(value) {
  return value.replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
}

function slugify(value) {
  return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function inlineMarkdown(value) {
  let html = escapeHtml(value);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]+&quot;)?\)/g, (_, label, href) => {
    if (href.startsWith("#") && activePage) return `<a href="#page=${activePage}&section=${encodeURIComponent(href.slice(1))}">${label}</a>`;
    if (/(?:^|\/)README\.md$/i.test(href)) return `<a href="#home">${label}</a>`;
    const match = href.match(/(?:^|\/)([\w-]+)\.md(?:#(.*))?$/);
    if (match && pageMap.has(match[1])) {
      const section = match[2] ? `&section=${encodeURIComponent(match[2])}` : "";
      return `<a href="#page=${match[1]}${section}">${label}</a>`;
    }
    if (!/^(https?:|mailto:)/.test(href)) return label;
    return `<a href="${href}" target="_blank" rel="noreferrer">${label}</a>`;
  });
  return html;
}

function renderTable(lines) {
  const cells = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((cell) => inlineMarkdown(cell.trim()));
  const header = cells(lines[0]);
  const rows = lines.slice(2).map(cells);
  return `<table><thead><tr>${header.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/^---[\s\S]*?---\s*/, "").replace(/<!--([\s\S]*?)-->/g, "").split("\n");
  const output = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }
    if (line.startsWith("```")) {
      const language = line.slice(3).trim(); const code = []; index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) code.push(lines[index++]);
      index += 1;
      output.push(`<pre><button class="copy-code" type="button">Copy</button><code class="language-${escapeHtml(language)}">${escapeHtml(code.join("\n"))}</code></pre>`); continue;
    }
    if (/^\|/.test(line) && /^\|?\s*:?-{3,}/.test(lines[index + 1] || "")) {
      const table = [line]; index += 1;
      while (index < lines.length && /^\|/.test(lines[index])) table.push(lines[index++]);
      output.push(renderTable(table)); continue;
    }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) { const level = heading[1].length; const text = heading[2]; const id = slugify(text); output.push(`<h${level} id="${id}">${inlineMarkdown(text)}</h${level}>`); index += 1; continue; }
    if (/^([-*_])\1\1+\s*$/.test(line)) { output.push("<hr>"); index += 1; continue; }
    if (line.startsWith(">")) { const quote = []; while (index < lines.length && lines[index].startsWith(">")) quote.push(lines[index++].replace(/^>\s?/, "")); output.push(`<blockquote>${markdownToHtml(quote.join("\n"))}</blockquote>`); continue; }
    if (/^[-*+]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
      const ordered = /^\d+\.\s+/.test(line); const tag = ordered ? "ol" : "ul"; const items = [];
      while (index < lines.length && (ordered ? /^\d+\.\s+/.test(lines[index]) : /^[-*+]\s+/.test(lines[index]))) items.push(lines[index++].replace(ordered ? /^\d+\.\s+/ : /^[-*+]\s+/, ""));
      output.push(`<${tag}>${items.map((item) => `<li>${inlineMarkdown(item)}</li>`).join("")}</${tag}>`); continue;
    }
    const paragraph = [line]; index += 1;
    while (index < lines.length && lines[index].trim() && !/^(#{1,3}\s|```|\||>|[-*+]\s+|\d+\.\s+)/.test(lines[index])) paragraph.push(lines[index++]);
    output.push(`<p>${inlineMarkdown(paragraph.join(" "))}</p>`);
  }
  return output.join("\n");
}

function updateNavigation(page) {
  document.querySelectorAll("[data-route]").forEach((link) => link.classList.toggle("active", link.dataset.route === (page || "home")));
  setNavigationOpen(false);
}

async function renderRoute() {
  const { page, section } = getRoute();
  const request = ++navigationRequest;
  updateNavigation(page);
  if (!page || !pageMap.has(page)) {
    home.hidden = false; documentView.hidden = true; document.title = "Compound GPID | Documentation"; return;
  }
  home.hidden = true; documentView.hidden = false; documentView.innerHTML = '<p class="loading">Loading canonical documentation...</p>';
  const config = pageMap.get(page); activePage = page; document.title = `${config.title} | Compound GPID`;
  try {
    const response = await fetch(config.file);
    if (!response.ok) throw new Error(`Could not load ${config.file}`);
    const markdown = await response.text();
    if (request !== navigationRequest) return;
    documentView.innerHTML = markdownToHtml(markdown);
    documentView.querySelectorAll(".copy-code").forEach((button) => button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.nextElementSibling.textContent);
      button.textContent = "Copied"; setTimeout(() => { button.textContent = "Copy"; }, 1300);
    }));
    const target = section && document.getElementById(section);
    (target || documentView).scrollIntoView({ behavior: "instant", block: "start" });
    document.getElementById("content").focus({ preventScroll: true });
  } catch (error) {
    if (request !== navigationRequest) return;
    documentView.innerHTML = `<p class="error-message">This documentation page could not be loaded. <a href="${config.file}">Open the canonical Markdown file</a>.</p>`;
  }
}

async function buildSearchIndex() {
  if (searchIndex) return searchIndex;
  const source = await Promise.all(pages.map(async ([id, title, file]) => {
    try { const text = await (await fetch(file)).text(); return { id, title, text: text.replace(/[#*`>|\[\]()]/g, " ").replace(/\s+/g, " ") }; } catch { return { id, title, text: "" }; }
  }));
  searchIndex = source; return source;
}

async function search(query) {
  const term = query.trim().toLowerCase(); activeResult = -1;
  if (!term) { searchResults.innerHTML = '<p class="search-hint">Search all public documentation. Try <code>install</code>, <code>review</code>, or <code>cg-update</code>.</p>'; return; }
  searchResults.innerHTML = '<p class="search-hint">Searching canonical documentation...</p>';
  const index = await buildSearchIndex();
  const results = index.filter((entry) => `${entry.title} ${entry.text}`.toLowerCase().includes(term)).slice(0, 8);
  searchResults.innerHTML = results.length ? results.map((entry) => {
    const at = entry.text.toLowerCase().indexOf(term); const excerpt = at >= 0 ? entry.text.slice(Math.max(0, at - 60), at + term.length + 110) : "";
    return `<a class="search-result" href="#page=${entry.id}"><small>${entry.title}</small><strong>${entry.title}</strong><p>${escapeHtml(excerpt)}...</p></a>`;
  }).join("") : '<p class="search-hint">No matching documentation. Try a command name or a shorter phrase.</p>';
}

function openSearch() { if (!searchDialog.open) searchDialog.showModal(); setTimeout(() => searchInput.focus(), 0); }
function closeSearchOnRoute() { if (searchDialog.open) searchDialog.close(); }
document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", openSearch));
searchInput.addEventListener("input", (event) => search(event.target.value));
searchResults.addEventListener("click", closeSearchOnRoute);
document.querySelector("[data-close-search]").addEventListener("click", () => searchDialog.close());
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openSearch(); }
  if (!searchDialog.open || !["ArrowDown", "ArrowUp", "Enter"].includes(event.key)) return;
  const results = [...searchResults.querySelectorAll(".search-result")]; if (!results.length) return;
  if (event.key === "Enter" && activeResult >= 0) { results[activeResult].click(); return; }
  event.preventDefault(); activeResult = event.key === "ArrowDown" ? (activeResult + 1) % results.length : (activeResult - 1 + results.length) % results.length;
  results.forEach((result, index) => result.classList.toggle("selected", index === activeResult)); results[activeResult].scrollIntoView({ block: "nearest" });
});
function setNavigationOpen(opened) {
  const mobile = window.matchMedia("(max-width: 820px)").matches;
  sidebar.classList.toggle("open", opened && mobile);
  sidebar.inert = mobile && !opened;
  sidebar.setAttribute("aria-hidden", String(mobile && !opened));
  menuButton.setAttribute("aria-expanded", String(opened && mobile));
  if (opened && mobile) sidebar.querySelector("a").focus();
}
menuButton.addEventListener("click", () => setNavigationOpen(!sidebar.classList.contains("open")));
document.querySelector("[data-theme-toggle]").addEventListener("click", () => { const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = next; localStorage.setItem("compound-theme", next); });
window.addEventListener("resize", () => setNavigationOpen(false));
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && sidebar.classList.contains("open")) setNavigationOpen(false); });
const savedTheme = localStorage.getItem("compound-theme"); if (savedTheme) document.documentElement.dataset.theme = savedTheme;
setNavigationOpen(false);
window.addEventListener("hashchange", renderRoute); renderRoute();
