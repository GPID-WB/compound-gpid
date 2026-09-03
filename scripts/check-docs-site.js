"use strict";
const { access, readFile, readdir } = require("node:fs/promises");
const { constants } = require("node:fs");
const path = require("node:path");

const root = process.cwd();
const docsRoot = process.env.CG_DOCS_ROOT
  ? path.resolve(process.env.CG_DOCS_ROOT)
  : path.join(root, "docs");

function slugify(value) {
  return value.toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
    .replace(/[^a-z0-9\s-]/g, "").replace(/[\s-]+/g, "-").replace(/(^-|-$)/g, "");
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
  const registry = JSON.parse(await readFile(path.join(root, ".github", "shared", "module-registry.json"), "utf8"));
  const modules = new Map(registry.modules.map((module) => [module.id, module]));
  const loadable = new Set();
  const visit = (moduleId) => {
    if (loadable.has(moduleId)) return;
    loadable.add(moduleId);
    for (const dependency of modules.get(moduleId)?.dependsOn || []) visit(dependency);
  };
  for (const module of registry.modules.filter((item) => item.layer === "suite")) visit(module.id);
  for (const capability of registry.capabilities || []) visit(capability.owningModule);
  const ownedPatterns = [...loadable]
    .flatMap((moduleId) => modules.get(moduleId)?.ownedAssets || []);
  const isOwned = (pattern, candidate) => {
    const directory = pattern.endsWith("/");
    const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&")
      .replaceAll("*", "[^/]*").replaceAll("?", "[^/]");
    return new RegExp(`^${escaped}${directory ? ".*" : ""}$`).test(candidate);
  };
  const canonical = new Set((await readdir(canonicalRoot, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && /^(?:cg|cr)-skill-/.test(entry.name))
    .filter((entry) => {
      const candidate = `.github/skills/${entry.name}/SKILL.md`;
      return ownedPatterns.some((pattern) => isOwned(pattern, candidate));
    })
    .map((entry) => entry.name));
  const catalogFiles = ["analysis.md", "development.md", "institutional.md", "research.md"]
    .map((file) => path.join(docsRoot, "skills", file));
  const catalogText = (await Promise.all(catalogFiles.map((file) => readFile(file, "utf8")))).join("\n");
  const catalogMatches = [...catalogText.matchAll(/\.github\/skills\/((?:cg|cr)-skill-[a-z-]+)\/SKILL\.md/g)]
    .map((match) => match[1]);
  const technicalCanonical = new Set(
    [...canonical].filter((skill) => skill.startsWith("cg-skill-"))
  );
  const technicalCatalog = new Set(catalogMatches.filter((skill) => skill.startsWith("cg-skill-")));
  const researchCanonical = new Set(
    [...canonical].filter((skill) => skill.startsWith("cr-skill-"))
  );
  const researchCatalog = new Set(catalogMatches.filter((skill) => skill.startsWith("cr-skill-")));
  const missing = [...technicalCanonical].filter((skill) => !technicalCatalog.has(skill));
  const unknown = [...technicalCatalog].filter((skill) => !technicalCanonical.has(skill));
  const missingResearch = [...researchCanonical].filter((skill) => !researchCatalog.has(skill));
  const unknownResearch = [...researchCatalog].filter(
    (skill) => !canonical.has(skill)
  );
  if (missing.length || unknown.length || missingResearch.length || unknownResearch.length
    || technicalCatalog.size !== technicalCanonical.size
    || researchCatalog.size !== researchCanonical.size
    || catalogMatches.length !== new Set(catalogMatches).size) {
    throw new Error(`Skills catalog drift. Missing: ${[...missing, ...missingResearch].join(", ") || "none"}. Unknown: ${[...unknown, ...unknownResearch].join(", ") || "none"}.`);
  }
  for (const skill of canonical) await access(path.join(canonicalRoot, skill, "SKILL.md"), constants.R_OK);
}

async function loadCandidatePages() {
  const manifestPath = path.join(docsRoot, "skills", "management", "candidates.json");
  let manifest;
  try {
    manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
  if (manifest.schemaVersion !== "compound-gpid-docs-candidates-v1"
      || !Array.isArray(manifest.pages)) {
    throw new Error("Unexpected candidate documentation manifest schema.");
  }
  const ids = manifest.pages.map((page) => page.id);
  const files = manifest.pages.map((page) => page.file);
  if (new Set(ids).size !== ids.length) throw new Error("Candidate documentation page IDs must be unique.");
  if (new Set(files).size !== files.length) throw new Error("Candidate documentation files must be unique.");
  for (const page of manifest.pages) {
    if (!page.title || !page.description) throw new Error(`Candidate metadata is incomplete for ${page.id}.`);
    if (!page.file.startsWith("docs/skills/management/") || !page.file.endsWith(".md") || page.file.includes("..")) {
      throw new Error(`Candidate documentation file is unsafe: ${page.file}`);
    }
  }
  return manifest.pages;
}

(async () => {
  const requiredFiles = [
    path.join(docsRoot, "index.html"), path.join(docsRoot, "navigation.json"),
    path.join(docsRoot, "assets", "site.css"), path.join(docsRoot, "assets", "site.js"),
    path.join(docsRoot, ".nojekyll")
  ];
  for (const file of requiredFiles) await access(file, constants.R_OK);

  const manifest = JSON.parse(await readFile(path.join(docsRoot, "navigation.json"), "utf8"));
  if (manifest.schemaVersion !== "compound-gpid-docs-navigation-v1") {
    throw new Error("Unexpected documentation navigation schema version.");
  }
  if (!Array.isArray(manifest.groups) || manifest.groups.length < 5) {
    throw new Error("Documentation navigation must contain audience-oriented groups.");
  }
  const pages = manifest.groups.flatMap((group) => group.pages || []);
  const candidatePages = await loadCandidatePages();
  const ids = pages.map((page) => page.id);
  const pageFiles = pages.map((page) => page.file);
  if (new Set(ids).size !== ids.length) throw new Error("Documentation page IDs must be unique.");
  if (new Set(pageFiles).size !== pageFiles.length) throw new Error("Documentation files must appear only once in navigation.");
  const candidateIds = new Set(candidatePages.map((page) => page.id));
  const candidateFiles = new Set(candidatePages.map((page) => page.file));
  if (ids.some((id) => candidateIds.has(id)) || pageFiles.some((file) => candidateFiles.has(`docs/${file}`))) {
    throw new Error("Candidate documentation must remain outside public navigation until migration.");
  }
  for (const page of pages) {
    if (!/^[a-z0-9-]+$/.test(page.id)) throw new Error(`Documentation page ID is unsafe: ${page.id}`);
    if (!/^[a-z0-9][a-z0-9./-]*\.md$/.test(page.file) || page.file.includes("..")) {
      throw new Error(`Documentation page file is unsafe: ${page.file}`);
    }
  }
  const requiredRoutes = new Map([
    ["philosophy", "philosophy.md"], ["getting-started", "getting-started/index.md"], ["why-compound-gpid", "why-compound-gpid.md"],
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
  const candidates = new Set(candidatePages.map((page) => path.normalize(path.join(root, page.file))));
  const orphaned = markdownFiles.filter((file) => !represented.has(file) && !candidates.has(file));
  const missing = [...represented].filter((file) => !markdownFiles.includes(file));
  if (orphaned.length || missing.length) {
    throw new Error(`Navigation coverage failed. Orphaned: ${orphaned.map((file) => path.relative(root, file)).join(", ") || "none"}. Missing: ${missing.map((file) => path.relative(root, file)).join(", ") || "none"}.`);
  }

  for (const page of pages) {
    if (!page.title || !page.description) throw new Error(`Navigation metadata is incomplete for ${page.id}.`);
    const content = await readFile(path.join(docsRoot, page.file), "utf8");
    if (!/^\uFEFF?#\s+\S/m.test(content)) throw new Error(`${page.file} must have a level-one heading.`);
  }
  for (const page of candidatePages) {
    const content = await readFile(path.join(root, page.file), "utf8");
    if (!/^\uFEFF?#\s+\S/m.test(content)) throw new Error(`${page.file} must have a level-one heading.`);
  }

  const html = await readFile(path.join(docsRoot, "index.html"), "utf8");
  for (const semantic of ["<main", "<nav", "<dialog", "skip-link", "aria-controls=\"sidebar\""]) {
    if (!html.includes(semantic)) throw new Error(`Site shell is missing accessibility semantic: ${semantic}`);
  }
  const shellRoutes = [...html.matchAll(/#page=([a-z-]+)/g)].map((match) => match[1]);
  const unknownShellRoutes = shellRoutes.filter((id) => !ids.includes(id));
  if (unknownShellRoutes.length) throw new Error(`Site shell references unknown routes: ${unknownShellRoutes.join(", ")}.`);
  const siteScript = await readFile(path.join(docsRoot, "assets", "site.js"), "utf8");
  for (const contract of ["navigation.json", "navigationRequest", "aria-current", "setNavigationOpen", "#{1,6}"]) {
    if (!siteScript.includes(contract)) throw new Error(`Site runtime is missing contract: ${contract}`);
  }

  const workflow = await readFile(".github/workflows/pages.yml", "utf8");
  const releasePagesWorkflow = await readFile(".github/workflows/release-pages.yml", "utf8");
  for (const action of ["actions/configure-pages", "actions/upload-pages-artifact", "actions/deploy-pages"]) {
    if (!workflow.includes(action) || !releasePagesWorkflow.includes(action)) {
      throw new Error(`Pages controllers must use ${action}.`);
    }
  }
  if (!workflow.includes("path: site-artifact/docs") || !releasePagesWorkflow.includes("path: release-artifact/docs")) {
    throw new Error("Pages workflow must upload verified main and release documentation artifacts.");
  }

  // -------------------------------------------------------------------------
  // What's New route, page, heading, and release marker pair.
  // -------------------------------------------------------------------------
  const whatsNewPage = pages.find((page) => page.id === "whats-new");
  if (!whatsNewPage) throw new Error("Documentation must expose a what's-new route.");
  if (whatsNewPage.file !== "whats-new.md") throw new Error("What's New route must target whats-new.md.");
  const whatsNewContent = await readFile(path.join(docsRoot, whatsNewPage.file), "utf8");
  if (!/^\uFEFF?#\s+What.s New/m.test(whatsNewContent)) {
    throw new Error("docs/whats-new.md must have a level-one What's New heading.");
  }
  const releaseOpen = whatsNewContent.indexOf("<!-- cg:auto:release-notes -->");
  const releaseClose = whatsNewContent.indexOf("<!-- cg:auto:end -->");
  if (releaseOpen === -1 || releaseClose === -1 || releaseClose < releaseOpen) {
    throw new Error("docs/whats-new.md must contain a paired release-notes marker.");
  }

  // -------------------------------------------------------------------------
  // Split Technical/Research prompt markers in reference.md (marker migration).
  // -------------------------------------------------------------------------
  const referenceContent = await readFile(path.join(docsRoot, "reference.md"), "utf8");
  const cmdOpen = (referenceContent.match(/<!-- cg:auto:commands -->/g) || []).length;
  const cmdClose = (referenceContent.match(/<!-- cg:auto:end -->/g) || []).length;
  const researchOpen = (referenceContent.match(/<!-- cg:auto:research-commands -->/g) || []).length;
  if (cmdOpen !== 1 || cmdClose !== 2 || researchOpen !== 1) {
    throw new Error("reference.md markers must be a single commands pair plus a research-commands pair.");
  }
  const commandsPos = referenceContent.indexOf("<!-- cg:auto:commands -->");
  const researchPos = referenceContent.indexOf("<!-- cg:auto:research-commands -->");
  const commandsClose = referenceContent.indexOf("<!-- cg:auto:end -->");
  const researchClose = referenceContent.indexOf("<!-- cg:auto:end -->", commandsClose + 1);
  if (!(commandsPos < commandsClose && commandsClose < researchPos && researchPos < researchClose)) {
    throw new Error("commands and research-commands markers must be ordered and non-overlapping.");
  }

  // -------------------------------------------------------------------------
  // Complete-build artifact handoff and freshness contract.
  // -------------------------------------------------------------------------
  const rebuildWorkflow = await readFile(".github/workflows/doc-rebuild.yml", "utf8");
  const releaseWorkflow = await readFile(".github/workflows/release-docs.yml", "utf8");
  const rebuildContract = [
    "branches: [main]",
    "contents: write",
    "rebuild-docs.js --all",
    "git diff --quiet -- docs/",
    "git add -- docs/",
    "docs-site",
    ".docs-build-metadata.json",
  ];
  for (const token of rebuildContract) {
    if (!rebuildWorkflow.includes(token)) throw new Error(`doc-rebuild.yml must reference ${token}.`);
  }
  if (!rebuildWorkflow.includes("include-hidden-files: true")) {
    throw new Error("doc-rebuild.yml must include hidden artifact files.");
  }
  const releaseContract = [
    "name: Build release documentation",
    "tags: [\"v*.*.*\"]",
    "contents: read",
    "rebuild-docs.js --all",
    "--validate-release-set",
    "release-docs-site",
    ".docs-build-metadata.json",
  ];
  for (const token of releaseContract) {
    if (!releaseWorkflow.includes(token)) throw new Error(`release-docs.yml must reference ${token}.`);
  }
  if (/pages:\s*write|id-token:\s*write/.test(releaseWorkflow)) {
    throw new Error("release-docs.yml must remain unprivileged.");
  }
  if (!/workflow_run\s*:/.test(workflow)) {
    throw new Error("pages.yml must consume doc-rebuild via workflow_run.");
  }
  const pagesContract = [
    "Rebuild documentation",
    "actions/download-artifact",
    "run-id:",
    "--verify-artifact",
    "--verify-fingerprint",
    "site-artifact/docs",
  ];
  for (const token of pagesContract) {
    if (!workflow.includes(token)) throw new Error(`pages.yml must reference ${token}.`);
  }
  const releasePagesContract = [
    "Build release documentation",
    "release-docs-site",
    "release-artifact/docs",
    "Artifact digest mismatch",
    "Deploy docs from",
    "Refusing to deploy an older release artifact",
    "Recheck release is still newest",
  ];
  for (const token of releasePagesContract) {
    if (!releasePagesWorkflow.includes(token)) throw new Error(`release-pages.yml must reference ${token}.`);
  }

  await validateMarkdownLinks(markdownFiles);
  await validateSkillsCatalog();
  console.log(`Documentation site check passed (${pages.length} navigable Markdown pages, ${manifest.groups.length} groups, complete skills catalog).`);
})().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
