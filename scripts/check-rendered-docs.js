"use strict";
const fs = require("node:fs");
const path = require("node:path");

/** Validate navigable HTML, local assets, anchors, and search destinations. */
function checkRendered(directory) {
  const root = path.resolve(directory);
  const metadata = JSON.parse(fs.readFileSync(path.join(root, "site-build.json"), "utf8"));
  const files = fs.readdirSync(root).filter(file => file === "index.html" || /^p-.+\.html$/.test(file));
  if (files.length !== metadata.pages + 1) throw new Error("Rendered page count does not match the build.");
  const documents = new Map(files.map(file => [file, fs.readFileSync(path.join(root, file), "utf8")]));
  const errors = [];
  function destination(href, source) {
    const value = href.replace(/&amp;/g, "&");
    if (/^(https?:|mailto:)/.test(value)) return;
    const [relative, fragment] = value.split("#");
    const target = relative || source;
    const full = path.resolve(root, target);
    if (!full.startsWith(`${root}${path.sep}`) || !fs.existsSync(full)) {
      errors.push(`${source}: missing destination ${value}`);
    } else if (fragment && documents.has(target)) {
      if (!documents.get(target).includes(`id="${decodeURIComponent(fragment)}"`)) errors.push(`${source}: missing anchor ${value}`);
    }
  }
  for (const [file, html] of documents) {
    if (!/<body[^>]*data-rendered="true"/.test(html)) errors.push(`${file}: missing render marker`);
    if (file !== "index.html" && !/<article[^>]*data-document[^>]*>\s*<h1/.test(html)) errors.push(`${file}: article is not pre-rendered`);
    for (const [, href] of html.matchAll(/(?:href|src)="([^"]+)"/g)) destination(href, file);
  }
  const index = JSON.parse(fs.readFileSync(path.join(root, "search-index.json"), "utf8"));
  if (new Set(index.map(record => record.id)).size !== metadata.pages) errors.push("Search coverage differs from the rendered pages.");
  for (const record of index) destination(`p-${record.id}.html${record.section ? `#${record.section}` : ""}`, "search-index.json");
  if (errors.length) throw new Error([...new Set(errors)].join("\n"));
  return { pages: metadata.pages, sections: index.length };
}
if (require.main === module) {
  try { console.log(`Rendered documentation check passed: ${JSON.stringify(checkRendered(process.argv[2] || ".site"))}`); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { checkRendered };
