"use strict";
// Build ordinary HTML and a section-aware search index without runtime services.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { escape, href, staticLinks, navigation, reader } = require("./docs-html.js");

/** Render a canonical docs tree into a separate, disposable site directory. */
function renderSite({ docsRoot, out, channel = "dev", sha = "", preserveOtherFiles = false }) {
  docsRoot = path.resolve(docsRoot);
  out = path.resolve(out);
  if (out === docsRoot || docsRoot.startsWith(`${out}${path.sep}`) || out.startsWith(`${docsRoot}${path.sep}`)) {
    throw new Error("Rendered output must be separate from the canonical docs tree.");
  }
  if (!["main", "dev"].includes(channel)) throw new Error("Unknown documentation channel.");
  if (sha && !/^[0-9a-f]{40}$/i.test(sha)) throw new Error("Source SHA must be a full commit identity.");
  const manifest = JSON.parse(fs.readFileSync(path.join(docsRoot, "navigation.json"), "utf8"));
  const pages = manifest.groups.flatMap(group => group.pages.map(page => ({ ...page, group: group.title })));
  for (const page of pages) {
    if (!/^[a-z0-9-]+$/.test(page.id) || !/^[a-z0-9][a-z0-9./-]*\.md$/.test(page.file) || page.file.includes("..")) {
      throw new Error("Unsafe page identity in navigation.");
    }
  }
  if (new Set(pages.map(page => page.id)).size !== pages.length) throw new Error("Duplicate page identity.");
  const shell = fs.readFileSync(path.join(docsRoot, "index.html"), "utf8");
  if (!shell.includes("<!-- home:start -->") || !shell.includes("<!-- reader:start -->")) {
    throw new Error("Site shell is missing static-rendering boundaries.");
  }
  // Reuse the exact browser renderer and anchors; only its environment is supplied.
  const context = vm.createContext({
    URL, Map, activePage: "",
    pageMap: new Map(pages.map(page => [page.id, page])),
    fileMap: new Map(pages.map(page => [page.file, page])),
    document: { body: { dataset: { channel } } },
  });
  vm.runInContext(fs.readFileSync(path.join(docsRoot, "assets/search-model.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(docsRoot, "assets/markdown.js"), "utf8"), context);
  if (fs.existsSync(out)) {
    if (fs.lstatSync(out).isSymbolicLink()) throw new Error("Rendered output must not be a symbolic link.");
    // The combined assembler uses a fresh staging tree containing both channels.
    if (!preserveOtherFiles) fs.rmSync(out, { recursive: true });
  }
  fs.mkdirSync(out, { recursive: true });
  fs.cpSync(docsRoot, out, { recursive: true, dereference: false, filter(source) {
    if (fs.lstatSync(source).isSymbolicLink()) throw new Error(`Symbolic link in docs: ${source}`);
    return true;
  } });
  const noScript = '<noscript><style>[data-open-search],[data-nav-filter],label[for="nav-filter"],.menu-button,[data-theme-toggle],.copy-code{display:none!important}.no-script-only{display:block}@media(max-width:820px){.sidebar{position:static;transform:none;width:100%;height:auto;box-shadow:none}.home-mode>.sidebar{display:none}}</style></noscript>';
  const stamp = sha ? `<p class="build-stamp">${channel === "dev" ? "Development" : "Stable"} documentation · Source <a href="https://github.com/GPID-WB/compound-gpid/commit/${sha}">${sha.slice(0, 7)}</a> · Rendered by the documentation build</p>` : "";
  function frame(content, page) {
    let html = content.replace('<body>', `<body data-rendered="true" data-channel="${channel}"${page ? ` data-page="${page.id}"` : ""}>`);
    html = html.replace(/(<nav class="nav-list"[^>]*>)[^]*?<\/nav>/, (_, open) => `${open}${navigation(manifest.groups, page?.id)}</nav>`);
    html = html.replace('<span data-page-count></span>', `<span data-page-count>${pages.length} guides and references</span>`);
    html = html.replace('<div class="directory-grid" data-doc-map></div>', `<div class="directory-grid" data-doc-map>${manifest.groups.map(group => `<a href="${href(group.pages[0].id)}"><h3>${escape(group.title)} <span aria-hidden="true">→</span></h3><p>${escape(group.description)}</p><small>${group.pages.length} pages</small></a>`).join("")}</div>`);
    html = html.replace(/(<span class="channel-badge"[^>]*>)[^<]+/, `$1${channel === "dev" ? "Development" : "Stable"}`);
    html = html.replace(/<a class="channel-link"[^]*?<\/a>/, `<a class="channel-link" data-other-channel href="https://gpid-wb.github.io/compound-gpid/${channel === "dev" ? "" : "dev/"}">View ${channel === "dev" ? "stable" : "latest development"} docs →</a>`);
    html = html.replace(/<noscript>[^]*?<\/noscript>/g, noScript);
    html = html.replace('</main>', `${stamp}</main>`);
    if (page) {
      html = html.replace('<title>Compound GPID | Documentation</title>', `<title>${escape(page.title)} | Compound GPID</title>`)
        .replace(/<meta name="description"[^>]*>/, `<meta name="description" content="${escape(page.description)}">`)
        .replace('class="site-frame home-mode"', 'class="site-frame"');
    }
    return staticLinks(html, page?.id);
  }
  fs.writeFileSync(path.join(out, "index.html"), frame(shell));
  const index = [];
  for (const page of pages) {
    const markdown = fs.readFileSync(path.join(docsRoot, page.file), "utf8");
    context.activePage = page.id;
    const article = context.markdownToHtml(markdown);
    const group = manifest.groups.find(group => group.title === page.group);
    let html = shell.replace(/<!-- home:start -->[^]*?<!-- home:end -->/, '<section class="home-page" data-home hidden></section>');
    html = html.replace(/<!-- reader:start -->[^]*?<!-- reader:end -->/, reader(page, group, article, channel));
    fs.writeFileSync(path.join(out, href(page.id)), frame(html, page));
    index.push(...context.DocsSearch.records(page, markdown));
  }
  fs.writeFileSync(path.join(out, "search-index.json"), `${JSON.stringify(index)}\n`);
  fs.writeFileSync(path.join(out, "site-build.json"), `${JSON.stringify({ schemaVersion: 1, channel, sourceSha: sha, pages: pages.length })}\n`);
  return { pages: pages.length, sections: index.length };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const options = { docsRoot: path.resolve("docs"), out: path.resolve(".site"), channel: "dev" };
  const keys = { "--docs-root": "docsRoot", "--out": "out", "--channel": "channel", "--sha": "sha" };
  try {
    for (let i = 0; i < args.length; i += 2) {
      if (!keys[args[i]] || !args[i + 1]) throw new Error("Unknown or incomplete render argument.");
      options[keys[args[i]]] = args[i + 1];
    }
    console.log(`Rendered documentation: ${JSON.stringify(renderSite(options))}`);
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { renderSite };
