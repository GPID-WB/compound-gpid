"use strict";

// Deliberately pinned: recapture requires review, not the current working tree.
const revision = "9afd40ef4499da1b1cc9ade18e20ab596e4af6d2";
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");
const root = path.resolve(__dirname, "../../../..");
const contract = require(path.join(root, "docs/assets/docs-contract.js"));
const targets = require("./migration-targets.json");
const sha256 = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const source = file => execFileSync("git", ["show", `${revision}:${file}`], { cwd: root, maxBuffer: 8 * 1024 * 1024 });
const outputs = new Map();
const json = value => Buffer.from(`${JSON.stringify(value, null, 2)}\n`);
const files = ["docs/index.html", "docs/navigation.json", "docs/assets/site.js", "docs/assets/site.css",
  "scripts/rebuild-docs.js", "scripts/docs-markers.js", "scripts/generate-whats-new.js", "scripts/release-payloads.js", "scripts/release-version.js",
  "scripts/check-docs-site.js", "scripts/assemble-docs-site.js"];
const captured = {};
for (const file of files) {
  const bytes = source(file);
  outputs.set(`legacy/${file}`, bytes);
  captured[file] = sha256(bytes);
}
const runtime = outputs.get("legacy/docs/assets/site.js").toString();
const context = vm.createContext({ document: { querySelector: () => ({}) }, URLSearchParams, location: { hash: "" } });
vm.runInContext(runtime.slice(0, runtime.indexOf('document.querySelectorAll("[data-open-search]")')), context);
const manifest = JSON.parse(outputs.get("legacy/docs/navigation.json"));
const pages = manifest.groups.flatMap(group => group.pages);
const documents = {};
const inventory = { schemaVersion: 1, sourceRevision: revision, routes: [], inboundLinks: [], referenceScope: ["docs/", "README.md", ".github/"], preservation: [] };
for (const page of pages) {
  const bytes = source(`docs/${page.file}`), text = bytes.toString();
  documents[page.file] = text;
  const headings = contract.extractHeadings(text);
  const rendered = vm.runInContext(`markdownToHtml(${JSON.stringify(text)})`, context);
  const oldIds = [...rendered.matchAll(/<h[1-6] id="([^"]*)"/g)].map(match => match[1]);
  const aliasInfo = contract.headingAliases(headings), decisions = {};
  for (const alias of aliasInfo.ambiguous) {
    // Preserve the shipped runtime's first DOM match, explicitly recorded below.
    const chosen = headings.find(h => h.legacy[0] === alias) || headings.find(h => h.id === alias);
    if (!chosen) throw new Error(`Needs reviewed alias decision: ${page.id}#${alias}`);
    decisions[alias] = { target: chosen.id, reason: "Preserve first matching heading in the shipped runtime; explicit collision resolution, not an inferred alias." };
  }
  inventory.routes.push({ id: page.id, file: page.file, sourceSha256: sha256(bytes),
    destination: { page: page.id, file: page.file }, legacyRenderedIds: oldIds,
    legacyValidatorClaims: [...text.matchAll(/^#{1,6}\s+(.+)$/gm)].map(m => ({ text: m[1], slug: contract.legacySlugs(m[1])[1] })),
    headings: headings.map(h => ({ text: h.text, level: h.level, legacyRuntime: h.legacy[0], legacyValidator: h.legacy[1],
      destination: { page: page.id, section: h.id } })), aliasDecisions: decisions });
  if (page.file.startsWith("skills/management/") || page.file === "skills/importing.md") {
    inventory.preservation.push({ id: page.id, file: page.file, sourceSha256: sha256(bytes),
      plannedDestination: targets.narratives[page.id] ? { page: "skill-management", section: targets.narratives[page.id] } : { page: page.id, section: null },
      blocks: text.trim().split(/\r?\n\s*\r?\n/).map(block => ({
        kind: /```|~~~|cg-skill .*--/.test(block) ? "example" : /must|never|only|cannot|do not|requires?|approval|quarantine|unsafe|warning|destructive/i.test(block) ? "safety" : "context",
        text: block.replace(/\r\n/g, "\n"),
      })) });
  }
}
const tracked = execFileSync("git", ["ls-tree", "-r", "--name-only", revision, "docs", "README.md", ".github"], { cwd: root, encoding: "utf8" }).trim().split("\n");
for (const file of tracked.filter(file => /\.(?:md|html|json)$/.test(file))) {
  const text = source(file).toString();
  for (const match of text.matchAll(/\[[^\]]+\]\(([^)\s]+)(?:\s+"[^"]*")?\)|(?:href=")(#page=[^"]+)/g)) {
    const href = match[1] || match[2];
    if (/^(?:https?:|mailto:)/i.test(href)) continue;
    const [relative, fragment] = href.split("#", 2);
    const resolved = relative ? path.posix.normalize(path.posix.join(path.posix.dirname(file), relative)) : file;
    if (resolved.startsWith("docs/") || href.startsWith("#page=")) inventory.inboundLinks.push({ source: file,
      line: text.slice(0, match.index).split("\n").length, href, target: resolved, fragment: fragment || null });
  }
}
outputs.set("migration-inventory.json", json(inventory));
outputs.set("legacy-documents.json", json(documents));
// Small byte-controlled corpus, evaluated by the actual captured v1 implementation.
const fingerprintInputs = {
  "docs/index.md": "# Fixture\r\n\r\n<!-- cg:auto:commands -->\r\ngenerated A\r\n<!-- cg:auto:end -->\r\nManual prose.\r\n",
  "docs/assets/site.js": "/* legacy fixture */\n",
  ".github/prompts/z.prompt.md": "# Z\n", ".github/prompts/a.prompt.md": "# A\n",
  ".github/shared/ignored-v1.json": "{\"notAnInputInV1\":true}\n",
  "scripts/rebuild-docs.js": outputs.get("legacy/scripts/rebuild-docs.js").toString(),
  "scripts/docs-markers.js": outputs.get("legacy/scripts/docs-markers.js").toString(),
};
outputs.set("fingerprint-inputs.json", json(fingerprintInputs));
outputs.set("provenance.json", json({ schemaVersion: 1, sourceRevision: revision,
  capture: "git show <sourceRevision>:<path>; never rebuilt with the upgraded producer",
  producerContract: "compound-gpid-docs-producer-v1", fingerprintVersion: 1,
  runtimeContract: "compound-gpid-docs-runtime-v1", headingContract: "compound-gpid-headings-v1", files: captured }));

const check = process.argv[2] === "--check";
if (!check && process.argv.length !== 2) throw new Error("Use no arguments to capture, or --check to verify.");
for (const [relative, bytes] of outputs) {
  const target = path.join(__dirname, relative);
  if (check) {
    if (!fs.existsSync(target) || !fs.readFileSync(target).equals(bytes)) throw new Error(`Baseline drift: ${relative}`);
  } else {
    if (fs.existsSync(target) && !fs.readFileSync(target).equals(bytes)) {
      const old = relative === "provenance.json" ? JSON.parse(fs.readFileSync(target)) : null;
      const next = relative === "provenance.json" ? JSON.parse(bytes) : null;
      const extensionOnly = old && old.sourceRevision === revision
        && Object.entries(old.files).every(([file, digest]) => next.files[file] === digest)
        && JSON.stringify({ ...old, files: {} }) === JSON.stringify({ ...next, files: {} });
      if (!extensionOnly) throw new Error(`Refusing to overwrite baseline: ${relative}`);
    }
    fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, bytes);
  }
}
console.log(`Docs baseline ${check ? "verified" : "captured"}: ${pages.length} routes, ${inventory.preservation.length} preservation pages, ${inventory.inboundLinks.length} inbound links, ${inventory.routes.reduce((n, p) => n + Object.keys(p.aliasDecisions).length, 0)} explicit alias decisions.`);
