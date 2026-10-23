/* Orient the reader without copying documentation into a second source. */
function buildReaderContext(config) {
  const context = document.querySelector("[data-page-context]");
  const branch = document.body.dataset.channel || "dev";
  context.innerHTML = `<nav aria-label="Breadcrumb"><a href="#home">Docs</a><span aria-hidden="true">/</span><span>${escapeHtml(config.group)}</span></nav><a class="source-link" href="https://github.com/GPID-WB/compound-gpid/blob/${branch}/docs/${config.file}" target="_blank" rel="noreferrer">View source ↗</a>`;
  const headings = [...documentView.querySelectorAll("h2, h3")];
  const outline = document.querySelector("[data-page-outline]");
  if (headings.length) {
    outline.innerHTML = `<details open><summary>On this page</summary><nav aria-label="On this page">${headings.map(heading => `<a class="outline-level-${heading.tagName.toLowerCase()}" href="#page=${config.id}&section=${encodeURIComponent(heading.id)}">${escapeHtml(heading.textContent)}</a>`).join("")}</nav></details>`;
    if (window.matchMedia("(max-width: 1100px)").matches) outline.querySelector("details").open = false;
  }
  const group = groups.find(group => group.title === config.group);
  const index = group.pages.findIndex(page => page.id === config.id);
  const previous = group.pages[index - 1];
  const next = group.pages[index + 1];
  const link = (page, label) => page ? `<a href="#page=${page.id}"><small>${label}</small><strong>${escapeHtml(page.title.replace(/`/g, ""))} →</strong></a>` : '<span></span>';
  document.querySelector("[data-page-footer]").innerHTML = `<p>Continue in ${escapeHtml(group.title)}</p><nav aria-label="Adjacent pages">${link(previous, "Previous")}${link(next, "Next")}</nav><a class="source-link" href="#page=documentation-publishing">How these docs are maintained</a>`;
}
