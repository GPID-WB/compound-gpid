"use strict";
// Shared static-page furniture. Content still comes from canonical Markdown.
const escape = value => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
const href = id => `p-${id}.html`;

/** Convert legacy hash routes to portable, sibling HTML pages. */
function staticLinks(html, activeId = "") {
  return html.replace(/href="#page=([a-z0-9-]+)(?:&(?:amp;)?section=([^"]+))?"/g,
    (_, id, section) => `href="${id === activeId && section ? "" : href(id)}${section ? `#${section}` : ""}"`)
    .replace(/href="#home"/g, 'href="index.html"');
}

/** Render navigation from the same manifest used by the browser and checks. */
function navigation(groups, activeId) {
  return `<a href="index.html" data-route="home"${!activeId ? ' aria-current="page" class="active"' : ""}>Documentation home</a>`
    + groups.map((group, index) => {
      const open = group.pages.some(page => page.id === activeId) || (!activeId && index === 0);
      let previousSection;
      const links = group.pages.map(page => {
        let heading = "";
        if (page.section && page.section !== previousSection) {
          heading = `<p class="nav-subheading">${escape(page.section)}</p>`;
          previousSection = page.section;
        }
        return `${heading}<a href="${href(page.id)}" data-route="${page.id}" title="${escape(page.description)}"${page.id === activeId ? ' class="active" aria-current="page"' : ""}>${escape(page.title.replace(/`/g, ""))}</a>`;
      }).join("");
      return `<details class="nav-group"${open ? " open" : ""}><summary>${escape(group.title)}<span>${group.pages.length}</span></summary>${links}</details>`;
    }).join("");
}

/** Render a complete reader, including usable no-JavaScript orientation links. */
function reader(page, group, html, channel) {
  const headings = [...html.matchAll(/<h([23]) id="([^"]+)">([^]*?)<\/h\1>/g)];
  const outline = headings.length ? `<details open><summary>On this page</summary><nav aria-label="On this page">${headings.map(([, level, id, title]) => `<a class="outline-level-h${level}" href="#${id}">${title.replace(/<[^>]+>/g, "")}</a>`).join("")}</nav></details>` : "";
  const index = group.pages.findIndex(item => item.id === page.id);
  const adjacent = (item, label) => item ? `<a href="${href(item.id)}"><small>${label}</small><strong>${escape(item.title.replace(/`/g, ""))} →</strong></a>` : "<span></span>";
  return `<div class="reader" data-reader>
    <div class="page-context" data-page-context><nav aria-label="Breadcrumb"><a href="index.html">Docs</a><span aria-hidden="true">/</span><a href="${href(group.pages[0].id)}">${escape(group.title)}</a></nav><a class="source-link" href="https://github.com/GPID-WB/compound-gpid/blob/${channel}/docs/${page.file}" target="_blank" rel="noreferrer">View source →</a></div>
    <aside class="page-outline" data-page-outline>${outline}</aside>
    <article class="doc-page prose" data-document aria-live="polite">${staticLinks(html, page.id)}</article>
    <footer class="page-footer" data-page-footer><p>Continue in ${escape(group.title)}</p><nav aria-label="Adjacent pages">${adjacent(group.pages[index - 1], "Previous")}${adjacent(group.pages[index + 1], "Next")}</nav><a class="source-link" href="p-documentation-publishing.html">How these docs are maintained</a></footer>
  </div>`;
}

module.exports = { escape, href, staticLinks, navigation, reader };
