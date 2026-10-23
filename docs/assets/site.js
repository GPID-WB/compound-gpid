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
let groups = [];
let activePage = "";
let navigationRequest = 0;

function getRoute() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  return { page: params.get("page"), section: params.get("section") };
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
  groups = manifest.groups;
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
  revealNavigation(page);
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
    document.querySelector("[data-reader]").hidden = true;
    document.title = "Compound GPID | Documentation";
    home.scrollIntoView({ behavior: "instant", block: "start" });
    document.querySelector("#content").focus({ preventScroll: true });
    return;
  }
  if (activePage === page && documentView.querySelector("h1")) {
    const target = section && document.getElementById(section);
    (target || documentView).scrollIntoView({ behavior: "instant", block: "start" });
    return;
  }
  home.hidden = true;
  documentView.hidden = false;
  document.querySelector("[data-reader]").hidden = false;
  document.querySelector("[data-page-outline]").replaceChildren();
  document.querySelector("[data-page-context]").replaceChildren();
  document.querySelector("[data-page-footer]").replaceChildren();
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
    buildReaderContext(config);
    documentView.querySelectorAll(".copy-code").forEach((button) => button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.nextElementSibling.textContent);
        button.textContent = "Copied";
      } catch { button.textContent = "Select and copy"; }
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

function openSearch() {
  if (!searchDialog.open) searchDialog.showModal();
  setTimeout(() => searchInput.focus(), 0);
}

function closeSearchOnRoute() { if (searchDialog.open) searchDialog.close(); }

function setNavigationOpen(opened) {
  const mobile = window.matchMedia("(max-width: 820px)").matches;
  const isOpen = opened && mobile;
  if (isOpen) {
    const top = document.querySelector(".topbar").getBoundingClientRect().bottom;
    document.documentElement.style.setProperty("--navigation-top", `${top}px`);
  }
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

document.querySelector(".skip-link").addEventListener("click", event => {
  event.preventDefault();
  document.querySelector("#content").focus();
});
document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", openSearch));
searchInput.addEventListener("input", (event) => search(event.target.value));
searchResults.addEventListener("click", closeSearchOnRoute);
document.querySelector("[data-close-search]").addEventListener("click", () => searchDialog.close());
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openSearch(); }
  if (!searchDialog.open || !["ArrowDown", "ArrowUp", "Enter"].includes(event.key)) return;
  const results = [...searchResults.querySelectorAll(".search-result")];
  if (!results.length) return;
  if (event.key === "Enter") {
    if (event.target === searchInput && activeResult >= 0) { event.preventDefault(); results[activeResult].click(); }
    return;
  }
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
  try { localStorage.setItem("compound-theme", next); } catch { /* Storage is optional. */ }
});
window.addEventListener("resize", () => setNavigationOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && sidebar.classList.contains("open")) setNavigationOpen(false);
});
let savedTheme;
try { savedTheme = localStorage.getItem("compound-theme"); } catch { /* Storage is optional. */ }
if (savedTheme) document.documentElement.dataset.theme = savedTheme;

(async () => {
  try {
    await loadManifest();
    configureChannel();
    document.querySelector("[data-nav-filter]").addEventListener("input", filterNavigation);
    setNavigationOpen(false);
    window.addEventListener("hashchange", renderRoute);
    await renderRoute();
  } catch (error) {
    navigation.innerHTML = '<p class="nav-loading">Navigation could not be loaded.</p>';
    home.hidden = true;
    documentView.hidden = false;
    documentView.innerHTML = `<h1>Documentation unavailable</h1><p>${escapeHtml(error.message)}</p>`;
    documentView.focus();
  }
})();
