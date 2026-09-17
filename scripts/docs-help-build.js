"use strict";
// Protected catalog documentation writer bridge and browser projection owner.
const fs = require("node:fs"), path = require("node:path");
const { execFileSync } = require("node:child_process");
const contract = require("../docs/assets/docs-contract.js");
const data = require("./docs-source.js");

/** Independently validate canonical help and compute docs/index output without writing. */
function prepareHelp(root) {
  const python = process.platform === "win32" ? "python" : "python3";
  const documents = JSON.parse(execFileSync(python,
    [path.join(__dirname, "cg_generate_help_catalog.py"), "--root", root, "--stdout-docs"],
    { encoding: "utf8", timeout: 60000, maxBuffer: 8388608 }));
  const catalog = JSON.parse(fs.readFileSync(data.unlinked(path.join(root, ".github/shared/help-catalog.json"))));
  const routes = JSON.parse(fs.readFileSync(data.unlinked(path.join(root, "docs/reference/command-routes.json"))));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/navigation.json")));
  const pages = contract.validateManifest(manifest), registered = new Map(pages.map(p => [p.id, p]));
  const ids = [...catalog.commands.map(c => c.id), ...catalog.workflows.map(w => `workflow:${w.id}`)].sort();
  if (routes.schemaVersion !== 1 || Object.keys(routes).sort().join() !== "routes,schemaVersion" ||
    JSON.stringify(Object.keys(routes.routes).sort()) !== JSON.stringify(ids)) throw Error("Command route inventory differs from validated catalog");
  for (const [id, route] of Object.entries(routes.routes)) {
    if (Object.keys(route).sort().join() !== "page,section" || !registered.has(route.page)) throw Error(`Invalid command route: ${id}`);
    const page = registered.get(route.page);
    const text = documents[page.file] ?? fs.readFileSync(path.join(root, "docs", page.file), "utf8");
    if (route.section && !contract.extractHeadings(text).some(h => h.id === route.section)) throw Error(`Missing command route heading: ${id}`);
  }
  const projection = { schemaVersion: "compound-gpid-docs-commands-v1", generatorVersion: catalog.generatorVersion,
    sourceDigest: catalog.sourceDigest, commands: catalog.commands.map(row => ({ ...row, route: routes.routes[row.id] })),
    workflows: catalog.workflows.map(row => ({ ...row, route: routes.routes[`workflow:${row.id}`] })) };
  const output = { ...documents, "assets/command-index.json": JSON.stringify(projection, null, 2) + "\n" };
  const files = Object.entries(output).map(([name, next]) => {
    const file = path.join(root, "docs", name);
    return { path: `docs/${name}`, next, changed: !fs.existsSync(file) || fs.readFileSync(file, "utf8") !== next };
  });
  return { documents, projection, files };
}
module.exports = { prepareHelp };
