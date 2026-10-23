/* Navigation and discovery share the canonical navigation.json manifest. */
function buildNavigation(groups) {
  document.querySelector("[data-page-count]").textContent = `${pages.length} guides and references`;
  document.querySelector("[data-doc-map]").innerHTML = groups.map(group => `<a href="#page=${group.pages[0].id}"><h3>${escapeHtml(group.title)} <span aria-hidden="true">↗</span></h3><p>${escapeHtml(group.description || "Browse this section.")}</p><small>${group.pages.length} pages</small></a>`).join("");
  navigation.innerHTML = '<a href="#home" data-route="home">Documentation home</a>';
  groups.forEach((group, index) => {
    const section = document.createElement("details");
    section.className = "nav-group";
    section.open = index === 0;
    section.innerHTML = `<summary>${escapeHtml(group.title)}<span>${group.pages.length}</span></summary>`;
    let previousSection;
    group.pages.forEach(page => {
      if (page.section && page.section !== previousSection) {
        const heading = document.createElement("p");
        heading.className = "nav-subheading";
        heading.textContent = page.section;
        section.append(heading);
        previousSection = page.section;
      }
      const link = document.createElement("a");
      link.href = `#page=${page.id}`;
      link.dataset.route = page.id;
      link.title = page.description;
      link.textContent = page.title.replace(/`/g, "");
      section.append(link);
    });
    navigation.append(section);
  });
}
function revealNavigation(page) {
  document.querySelector("[data-nav-filter]").value = "";
  filterNavigation();
  const link = navigation.querySelector(`[data-route="${CSS.escape(page || "home")}"]`);
  const group = link?.closest("details");
  if (group) group.open = true;
  if (link) requestAnimationFrame(() => link.scrollIntoView({ block: "nearest" }));
}
function filterNavigation() {
  const term = document.querySelector("[data-nav-filter]").value.trim().toLowerCase();
  navigation.querySelectorAll("details").forEach(group => {
    if (term && !group.dataset.filtering) {
      group.dataset.wasOpen = String(group.open);
      group.dataset.filtering = "true";
    }
    let matches = 0;
    group.querySelectorAll("a").forEach(link => {
      link.hidden = !!term && !`${link.textContent} ${link.title}`.toLowerCase().includes(term);
      if (!link.hidden) matches += 1;
    });
    group.querySelectorAll(".nav-subheading").forEach(heading => { heading.hidden = !!term; });
    group.hidden = matches === 0;
    if (term) group.open = true;
    else if (group.dataset.filtering) {
      group.open = group.dataset.wasOpen === "true";
      delete group.dataset.filtering;
    }
  });
  const empty = ![...navigation.querySelectorAll("details")].some(group => !group.hidden);
  document.querySelector("[data-nav-empty]").hidden = !empty;
}
async function buildSearchIndex() {
  if (searchIndex) return searchIndex;
  searchIndex = (async () => {
    const entries = [];
    let cursor = 0;
    let failed = 0;
    async function worker() {
      while (cursor < pages.length) {
        const page = pages[cursor++];
        try {
          const response = await fetch(page.file);
          if (!response.ok) throw Error("Page unavailable");
          entries.push(...DocsSearch.records(page, await response.text()));
        } catch {
          failed += 1;
          entries.push({ ...page, heading: "", section: "", text: "" });
        }
      }
    }
    await Promise.all(Array.from({ length: 6 }, worker));
    if (failed) searchIndex = null; // A later query retries transient failures.
    return { entries, failed };
  })();
  return searchIndex;
}
async function search(query) {
  const term = query.trim();
  activeResult = -1;
  const status = document.querySelector("[data-search-status]");
  if (!term) {
    status.textContent = "";
    searchResults.innerHTML = '<p class="search-hint">Try <code>install windows</code>, <code>research review</code>, or <code>cg-skill activate</code>. Results open the matching section.</p>';
    return;
  }
  status.textContent = "Searching documentation…";
  const { entries, failed } = await buildSearchIndex();
  if (searchInput.value !== query) return;
  const results = DocsSearch.rank(entries, term);
  status.textContent = `${results.length} matching pages${failed ? ` · ${failed} pages could not be loaded; type again to retry` : ""}`;
  searchResults.innerHTML = results.length ? results.slice(0, 20).map(entry => {
    const words = term.toLowerCase().split(/\s+/);
    const at = entry.text.toLowerCase().indexOf(words[0]);
    const excerpt = at >= 0 ? entry.text.slice(Math.max(0, at - 45), at + 145) : entry.description;
    const section = entry.section ? `&section=${encodeURIComponent(entry.section)}` : "";
    return `<a class="search-result" href="#page=${entry.id}${section}"><small>${escapeHtml(entry.group)}</small><strong>${escapeHtml(entry.title.replace(/`/g, ""))}</strong>${entry.heading ? `<span>${escapeHtml(entry.heading)}</span>` : ""}<p>${escapeHtml(excerpt)}…</p></a>`;
  }).join("") : '<p class="search-hint">No matches. Try fewer words, a command name, or a topic such as <code>installation</code>.</p>';
}
function configureChannel() {
  const development = !!document.querySelector(".dev-preview-banner");
  const current = development ? "Development" : "Stable";
  document.querySelector("[data-channel-label]").textContent = current;
  const other = document.querySelector("[data-other-channel]");
  other.textContent = development ? "View stable docs ↗" : "View latest development docs ↗";
  other.href = development ? "https://gpid-wb.github.io/compound-gpid/" : "https://gpid-wb.github.io/compound-gpid/dev/";
  document.body.dataset.channel = development ? "dev" : "main";
}
