"use strict";
const { access, readFile, readdir } = require("node:fs/promises");
const { constants } = require("node:fs");
const path = require("node:path");
const docsContract = require("../docs/assets/docs-contract.js");
const SOURCE_AUTHORITY = /:\s*["']?(?:write|write-all)\b|\benvironment\s*:|\bsecrets[.\[]|actions\/(?:configure-pages|upload-pages-artifact|deploy-pages|create-github-app-token)@/;

function parseArguments(argv) {
  const options = {
    sourceRoot: process.cwd(),
    docsRoot: process.env.CG_DOCS_ROOT ? path.resolve(process.env.CG_DOCS_ROOT) : null,
    legacy: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--source-root") options.sourceRoot = path.resolve(argv[++index]);
    else if (argument === "--docs-root") options.docsRoot = path.resolve(argv[++index]);
    else if (argument === "--legacy") options.legacy = true;
    else throw new Error(`Unknown argument: ${argument}`);
  }
  return options;
}

const options = parseArguments(process.argv.slice(2));
const root = options.sourceRoot;
const docsRoot = options.docsRoot || path.join(root, "docs");
const legacySource = options.legacy;

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

async function validateMarkdownLinks(files, pages, legacyHeadings) {
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
      const headings = docsContract.extractHeadings(targetContent);
      const config = pages.find(page => path.join(docsRoot, page.file) === target);
      const resolved = legacyHeadings
        ? { status: headings.some(h => h.legacy[0] === decodeURIComponent(fragment)) ? "resolved" : "missing" }
        : docsContract.resolveSection(headings, decodeURIComponent(fragment), config?.sectionAliases);
      if (resolved.status !== "resolved") {
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

function validatePagesWorkflows(builder, controller) {
  // Check each job separately: another job must not satisfy a missing guard.
  const content = (text) => text.replace(/^\s*#.*$/gm, "");
  builder = content(builder);
  controller = content(controller);
  const requireTokens = (text, name, tokens) => {
    for (const token of tokens) {
      if (!text.includes(token)) throw new Error(`${name} must reference ${token}.`);
    }
  };
  if (SOURCE_AUTHORITY.test(builder)) {
    throw new Error("pages.yml must remain unprivileged, without an environment or publication credentials.");
  }
  requireTokens(builder, "pages.yml", [
    "branches: [dev]", "contents: read", "ref: ${{ github.sha }}",
    "persist-credentials: false", "github.ref == 'refs/heads/dev'",
    "node scripts/rebuild-docs.js --all", "node scripts/check-docs-site.js",
    "actions/upload-artifact@", "name: legacy-dev-docs", ".docs-build-metadata.json",
    "include-hidden-files: true", "if-no-files-found: error",
  ]);
  if (/workflow_run:|actions\/download-artifact@/.test(builder)) {
    throw new Error("pages.yml must build its own exact dev source, not consume a prior artifact.");
  }
  requireTokens(controller, "release-pages.yml", [
    'workflows: ["Build release documentation", "Deploy documentation site"]',
    "types: [completed]", "group: pages", "cancel-in-progress: false",
  ]);
  const jobs = new Map([...controller.matchAll(/^  (deploy(?:-dev)?):\r?\n([\s\S]*?)(?=^  [\w-]+:\r?\n|$(?![\s\S]))/gm)]
    .map((match) => [match[1], match[2]]));
  for (const [name, artifact] of [["deploy", "release"], ["deploy-dev", "combined"]]) {
    const job = jobs.get(name);
    if (!job) throw new Error(`release-pages.yml must contain ${name}.`);
    if (name === "deploy") {
      const archive = job.match(/- name: Verify immutable archive bytes before extraction\r?\n([\s\S]*?)(?=\n      -)/)?.[1] || "";
      if (!archive.includes('node scripts/legacy-pages.js archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"')) {
        throw new Error("deploy must reference the exact release archive verification.");
      }
    }
    // Static-data arguments to trusted scripts are allowed; script paths are not.
    if (/rebuild-docs\.js|generate-whats-new\.js|(?:node|bash|sh|python)\s+["']?(?:\$GITHUB_WORKSPACE\/)?(?:sources\/|current-dev\/|release-source\/|dev-artifact\/|release-artifact\/)|working-directory:\s*(?:sources\/|current-dev|release-source|dev-artifact|release-artifact)/.test(job)) {
      throw new Error(`${name} must not execute mutable source or rebuild downloaded content.`);
    }
    requireTokens(job, name, [
      "ref: ${{ github.sha }}", "persist-credentials: false", "actions: read",
      "contents: read", "pages: write", "id-token: write", "name: github-pages",
      "github.event.workflow_run.conclusion == 'success'", "actions/download-artifact@",
      "artifact-ids: ${{ steps.authority.outputs.artifact_id }}",
      'node scripts/legacy-pages.js archive "$ARTIFACT_ID" "$ARTIFACT_DIGEST"',
      "actions/configure-pages@", "actions/upload-pages-artifact@", "actions/deploy-pages@",
      `path: ${artifact}-artifact/site`, "node scripts/assemble-docs-site.js",
      `--verify ${artifact}-artifact`,
      name === "deploy" ? "run-id: ${{ inputs.build_run_id || github.event.workflow_run.id }}" : "run-id: ${{ github.event.workflow_run.id }}",
    ]);
    const upload = job.indexOf("actions/upload-pages-artifact@");
    const deploy = job.indexOf("actions/deploy-pages@");
    const check = "node scripts/legacy-pages.js check";
    if (job.indexOf(check) < 0 || job.indexOf(check) > job.indexOf("actions/download-artifact@")
        || job.lastIndexOf(check) < upload || job.lastIndexOf(check) > deploy) {
      throw new Error(`${name} must recheck authority after upload and before deployment.`);
    }
  }
  requireTokens(jobs.get("deploy-dev"), "deploy-dev", [
    "ref: main", "path: sources/main", "ref: ${{ steps.authority.outputs.release_sha }}",
    "path: sources/dev", "node scripts/legacy-pages.js import-dev sources/dev dev-artifact",
    '--main-root sources/main --dev-root sources/dev',
    'branches/dev" --jq .commit.sha)', 'branches/main" --jq .commit.sha)',
  ]);
  requireTokens(jobs.get("deploy"), "deploy", [
    "Artifact digest mismatch", "Artifact file list mismatch", "merge-base --is-ancestor",
    "Refusing to deploy an older release artifact", "Recheck release is still newest",
    'cmp -s "release-validation/releases/$RELEASE_TAG.json" release-validation/releases/latest.json',
  ]);
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
   const pages = docsContract.validateManifest(manifest);
  const candidatePages = legacySource ? [] : await loadCandidatePages();
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
    ["help", "help/index.md"], ["reference", "reference.md"],
    ...(legacySource ? [] : [
      ["research", "research/index.md"], ["research-philosophy", "research/philosophy.md"],
      ["research-first-workflow", "research/first-workflow.md"],
      ["research-short-example", "research/short-example.md"],
      ["research-lifecycle", "research/lifecycle.md"],
      ["research-evidence-boundaries", "research/evidence-boundaries.md"]
    ])
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

  const pageHeadings = {};
  for (const page of pages) {
    if (!page.title || !page.description) throw new Error(`Navigation metadata is incomplete for ${page.id}.`);
    const content = await readFile(path.join(docsRoot, page.file), "utf8");
    pageHeadings[page.id] = docsContract.extractHeadings(content);
    if (!pageHeadings[page.id].some(heading => heading.level === 1)) throw new Error(`${page.file} must have a level-one heading.`);
  }
  docsContract.validateManifest(manifest, pageHeadings);
  for (const page of candidatePages) {
    const content = await readFile(path.join(root, page.file), "utf8");
    if (!docsContract.extractHeadings(content).some(heading => heading.level === 1)) throw new Error(`${page.file} must have a level-one heading.`);
  }

  const html = await readFile(path.join(docsRoot, "index.html"), "utf8");
  for (const semantic of ["<main", "<nav", "<dialog", "skip-link", "aria-controls=\"sidebar\""]) {
    if (!html.includes(semantic)) throw new Error(`Site shell is missing accessibility semantic: ${semantic}`);
  }
  const shellRoutes = [...html.matchAll(/#page=([a-z-]+)/g)].map((match) => match[1]);
  const unknownShellRoutes = shellRoutes.filter((id) => !ids.includes(id));
  if (unknownShellRoutes.length) throw new Error(`Site shell references unknown routes: ${unknownShellRoutes.join(", ")}.`);
  const siteScript = await readFile(path.join(docsRoot, "assets", "site.js"), "utf8");
  const legacyHeadings = !siteScript.includes("DocsContract.parseDocument");
  if (!legacyHeadings && !html.includes('src="assets/docs-contract.js"')) throw new Error("Site shell must load the shared docs contract.");
  let readingScript = "";
  if (siteScript.includes("DocsReading.")) {
    const readingPosition = html.indexOf('src="assets/docs-reading.js"');
    if (readingPosition < 0 || readingPosition > html.indexOf('src="assets/site.js"')) throw new Error("Site shell must load reading controls before the runtime.");
    readingScript = await readFile(path.join(docsRoot, "assets", "docs-reading.js"), "utf8");
  }
  for (const contract of ["navigation.json", "navigationRequest", "aria-current", "setNavigationOpen"]) {
    if (!`${siteScript}\n${readingScript}`.includes(contract)) throw new Error(`Site runtime is missing contract: ${contract}`);
  }

  if (legacySource) {
    await validateMarkdownLinks(markdownFiles, pages, legacyHeadings);
    console.log(`Legacy documentation site check passed (${pages.length} navigable Markdown pages, ${manifest.groups.length} groups).`);
    return;
  }

  const workflow = await readFile(path.join(root, ".github/workflows/pages.yml"), "utf8");
  const combinedWorkflow = await readFile(path.join(root, ".github/workflows/docs-site-build.yml"), "utf8");
  const releasePagesWorkflow = await readFile(path.join(root, ".github/workflows/release-pages.yml"), "utf8");
  validatePagesWorkflows(workflow, releasePagesWorkflow);

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
  const rebuildWorkflow = await readFile(path.join(root, ".github/workflows/doc-rebuild.yml"), "utf8");
  const releaseWorkflow = await readFile(path.join(root, ".github/workflows/release-docs.yml"), "utf8");
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
  const combinedContract = [
    "name: Build combined documentation",
    "branches: [dev]",
    "Rebuild documentation",
    "assemble-docs-site.js",
    "combined-docs-site",
    ".docs-build-metadata.json",
  ];
  for (const token of combinedContract) {
    if (!combinedWorkflow.includes(token)) throw new Error(`docs-site-build.yml must reference ${token}.`);
  }
  if (SOURCE_AUTHORITY.test(combinedWorkflow.replace(/^\s*#.*$/gm, ""))) {
    throw new Error("docs-site-build.yml must remain unprivileged.");
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
  if (SOURCE_AUTHORITY.test(releaseWorkflow.replace(/^\s*#.*$/gm, ""))) {
    throw new Error("release-docs.yml must remain unprivileged.");
  }
  await validateMarkdownLinks(markdownFiles, pages, legacyHeadings);
  await validateSkillsCatalog();
  console.log(`Documentation site check passed (${pages.length} navigable Markdown pages, ${manifest.groups.length} groups, complete skills catalog).`);
})().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
