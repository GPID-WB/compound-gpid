const { access, readFile, readdir } = require("node:fs/promises");
const { constants } = require("node:fs");
const path = require("node:path");

const root = process.cwd();
const docsRoot = path.join(root, "docs");

function slugify(value) {
  return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

async function walkMarkdown(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const output = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) output.push(...await walkMarkdown(target));
    if (entry.isFile() && entry.name.endsWith(".md")) output.push(target);
  }
  return output;
}

function markdownHeadings(content) {
  return new Set([...content.matchAll(/^#{1,6}\s+(.+)$/gm)].map((match) => slugify(match[1])));
}

async function validateMarkdownLinks(files) {
  const errors = [];
  const contentCache = new Map();
  for (const file of files) contentCache.set(file, await readFile(file, "utf8"));

  for (const [file, content] of contentCache) {
    const links = [...content.matchAll(/\[[^\]]+\]\(([^)\s]+)(?:\s+"[^"]+")?\)/g)];
    for (const match of links) {
      const href = match[1];
      if (/^(https?:|mailto:)/i.test(href)) continue;
      const line = content.slice(0, match.index).split("\n").length;
      const [relativePath, fragment] = href.split("#", 2);
      const target = relativePath ? path.resolve(path.dirname(file), decodeURIComponent(relativePath)) : file;
      try {
        await access(target, constants.R_OK);
      } catch {
        errors.push(`${path.relative(root, file)}:${line} targets missing ${path.relative(root, target)}`);
        continue;
      }
      if (!fragment || !target.endsWith(".md")) continue;
      const targetContent = contentCache.get(target) || await readFile(target, "utf8");
      if (!markdownHeadings(targetContent).has(decodeURIComponent(fragment))) {
        errors.push(`${path.relative(root, file)}:${line} targets missing fragment #${fragment} in ${path.relative(root, target)}`);
      }
    }
  }
  if (errors.length) throw new Error(`Invalid internal Markdown links:\n- ${errors.join("\n- ")}`);
}

async function validateSkillsCatalog() {
  const canonicalRoot = path.join(root, ".github", "skills");
  const canonical = new Set((await readdir(canonicalRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("cg-skill-"))
    .map((entry) => entry.name));
  const catalogFiles = ["analysis.md", "development.md", "institutional.md"]
    .map((file) => path.join(docsRoot, "skills", file));
  const catalogText = (await Promise.all(catalogFiles.map((file) => readFile(file, "utf8")))).join("\n");
  const catalogMatches = [...catalogText.matchAll(/\.github\/skills\/(cg-skill-[a-z-]+)\/SKILL\.md/g)]
    .map((match) => match[1]);
  const catalog = new Set(catalogMatches);
  const missing = [...canonical].filter((skill) => !catalog.has(skill));
  const unknown = [...catalog].filter((skill) => !canonical.has(skill));
  const categoryCounts = await Promise.all(catalogFiles.map(async (file) => {
    const content = await readFile(file, "utf8");
    return [...content.matchAll(/^\| `cg-skill-[a-z-]+` \|/gm)].length;
  }));
  if (missing.length || unknown.length || catalog.size !== canonical.size
    || catalogMatches.length !== canonical.size || categoryCounts.join(",") !== "8,8,6") {
    throw new Error(`Skills catalog drift. Missing: ${missing.join(", ") || "none"}. Unknown: ${unknown.join(", ") || "none"}.`);
  }
  for (const skill of canonical) await access(path.join(canonicalRoot, skill, "SKILL.md"), constants.R_OK);
}

(async () => {
  const requiredFiles = [
    "docs/index.html", "docs/navigation.json", "docs/assets/site.css",
    "docs/assets/site.js", "docs/.nojekyll"
  ];
  for (const file of requiredFiles) await access(file, constants.R_OK);

  const manifest = JSON.parse(await readFile("docs/navigation.json", "utf8"));
  if (manifest.schemaVersion !== "compound-gpid-docs-navigation-v1") {
    throw new Error("Unexpected documentation navigation schema version.");
  }
  if (!Array.isArray(manifest.groups) || manifest.groups.length < 5) {
    throw new Error("Documentation navigation must contain audience-oriented groups.");
  }
  const pages = manifest.groups.flatMap((group) => group.pages || []);
  const ids = pages.map((page) => page.id);
  const pageFiles = pages.map((page) => page.file);
  if (new Set(ids).size !== ids.length) throw new Error("Documentation page IDs must be unique.");
  if (new Set(pageFiles).size !== pageFiles.length) throw new Error("Documentation files must appear only once in navigation.");
  const requiredRoutes = new Map([
    ["getting-started", "getting-started/index.md"], ["why-compound-gpid", "why-compound-gpid.md"],
    ["workflows", "workflows/index.md"], ["skills", "skills/index.md"],
    ["configuration", "configuration/index.md"], ["governance", "governance/index.md"],
    ["help", "help/index.md"], ["reference", "reference.md"]
  ]);
  for (const [id, file] of requiredRoutes) {
    const page = pages.find((entry) => entry.id === id);
    if (!page || page.file !== file) throw new Error(`Required route ${id} must target ${file}.`);
  }

  const markdownFiles = (await walkMarkdown(docsRoot)).sort();
  const represented = new Set(pageFiles.map((file) => path.normalize(path.join(docsRoot, file))));
  const orphaned = markdownFiles.filter((file) => !represented.has(file));
  const missing = [...represented].filter((file) => !markdownFiles.includes(file));
  if (orphaned.length || missing.length) {
    throw new Error(`Navigation coverage failed. Orphaned: ${orphaned.map((file) => path.relative(root, file)).join(", ") || "none"}. Missing: ${missing.map((file) => path.relative(root, file)).join(", ") || "none"}.`);
  }

  for (const page of pages) {
    if (!page.title || !page.description) throw new Error(`Navigation metadata is incomplete for ${page.id}.`);
    const content = await readFile(path.join(docsRoot, page.file), "utf8");
    if (!/^\uFEFF?#\s+\S/m.test(content)) throw new Error(`${page.file} must have a level-one heading.`);
  }

  const html = await readFile("docs/index.html", "utf8");
  for (const semantic of ["<main", "<nav", "<dialog", "skip-link", "aria-controls=\"sidebar\""]) {
    if (!html.includes(semantic)) throw new Error(`Site shell is missing accessibility semantic: ${semantic}`);
  }
  const shellRoutes = [...html.matchAll(/#page=([a-z-]+)/g)].map((match) => match[1]);
  const unknownShellRoutes = shellRoutes.filter((id) => !ids.includes(id));
  if (unknownShellRoutes.length) throw new Error(`Site shell references unknown routes: ${unknownShellRoutes.join(", ")}.`);
  const siteScript = await readFile("docs/assets/site.js", "utf8");
  for (const contract of ["navigation.json", "navigationRequest", "aria-current", "setNavigationOpen", "#{1,6}"]) {
    if (!siteScript.includes(contract)) throw new Error(`Site runtime is missing contract: ${contract}`);
  }

  const workflow = await readFile(".github/workflows/pages.yml", "utf8");
  for (const action of ["actions/configure-pages", "actions/upload-pages-artifact", "actions/deploy-pages"]) {
    if (!workflow.includes(action)) throw new Error(`Pages workflow must use ${action}.`);
  }
  if (!workflow.includes("path: docs")) throw new Error("Pages workflow must upload the docs directory.");

  await validateMarkdownLinks(markdownFiles);
  await validateSkillsCatalog();
  console.log(`Documentation site check passed (${pages.length} navigable Markdown pages, ${manifest.groups.length} groups, complete skills catalog).`);
})().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
