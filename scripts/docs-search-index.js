"use strict";
const contract = require("../docs/assets/docs-contract.js");
const search = require("../docs/assets/docs-search.js");

// Controller callers supply pristine data. Never load a helper from a source tree.
// Strip supported inline delimiters, but never interpret code contents as markup.
function text(value, literal = false) {
  if (!literal) value = value.replace(/`([^`]+)`|\[([^\]]+)\]\([^)]*\)|\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)/g,
    (_, code, label, strong, emphasis) => code ?? text(label ?? strong ?? emphasis));
  return value.replace(/\s+/g, " ").trim();
}

/** Project navigation and Markdown into deterministic JSON; no reads, writes or code execution.
 * Example: generateSearchIndex({ manifest, documents: { 'guide.md': '# Guide' }, registry }).
 */
function generateSearchIndex({ manifest, documents, registry }) {
  const pages = contract.validateManifest(manifest), entries = [];
  if (!Array.isArray(registry?.modules) || !Array.isArray(registry?.capabilities)) throw new Error("Documentation search: missing module registry");
  const modules = new Map(registry.modules.map(module => [module.id, module]));
  if (modules.size !== registry.modules.length) throw new Error("Documentation search: duplicate module owner");
  for (const page of pages.filter(contract.searchable)) {
    const module = modules.get(page.ownerModule);
    if (!module) throw new Error(`Documentation search: unknown owner ${page.ownerModule}`);
    let suite;
    if (module.layer === "kernel") suite = "shared";
    else if (module.layer === "suite" && ["suite-cg", "suite-cr"].includes(module.id)) suite = module.id.slice(6);
    else if (module.layer === "capability") {
      const support = registry.capabilities.filter(row => row.owningModule === module.id).map(row => row.supportedSuites);
      if (!support.length || support.some(values => !Array.isArray(values) || !values.length
        || values.some(value => !["cg", "cr"].includes(value)) || new Set(values).size !== values.length)) {
        throw new Error(`Documentation search: missing or invalid support for ${module.id}`);
      }
      const normalized = support.map(values => [...values].sort().join(","));
      if (new Set(normalized).size !== 1) throw new Error(`Documentation search: ambiguous support for ${module.id}`);
      suite = support[0].length === 2 ? "shared" : support[0][0];
    } else throw new Error(`Documentation search: invalid owner ${module.id}`);
    if (!documents || !Object.hasOwn(documents, page.file) || typeof documents[page.file] !== "string") {
      throw new Error(`Documentation search: missing Markdown ${page.file}`);
    }
    const makeEntry = heading => ({ page: page.id, section: heading?.id || null,
      title: page.title, heading: heading ? text(heading.text) : "", text: "", suite, kind: heading ? "section" : "page" });
    let current = makeEntry(); entries.push(current);
    function visit(blocks) {
      for (const block of blocks) {
        if (block.type === "heading" && [2, 3].includes(block.level)) {
          current = makeEntry(block); entries.push(current);
        } else if (block.type === "list") {
          for (const item of block.items) visit(item.children);
        } else if (block.type === "quote") visit(block.children);
        else if (block.type !== "heading" || block.level !== 1) {
          const body = block.type === "table" ? block.lines.filter((_, index) => index !== 1).join(" ") : block.text;
          if (body) current.text += ` ${text(body, block.type === "code")}`;
        }
      }
    }
    visit(contract.parseDocument(documents[page.file]).blocks);
  }
  for (const entry of entries) entry.text = entry.text.trim();
  const index = { schemaVersion: "compound-gpid-docs-search-v1", headingContract: contract.headingContract, entries };
  search.validateIndex(index, manifest);
  return `${JSON.stringify(index, null, 2)}\n`;
}

module.exports = { generateSearchIndex };
