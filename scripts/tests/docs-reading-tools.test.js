"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const tools = () => require("../../docs/assets/docs-tools.js");
const sha = "a".repeat(40);

test("repository source links use an exact supplied SHA and validated repository paths", () => {
  assert.equal(tools().repositoryUrl("../.github/prompts/cg-work.prompt.md", "installation.md", sha),
    `https://github.com/GPID-WB/compound-gpid/blob/${sha}/.github/prompts/cg-work.prompt.md`);
  assert.equal(tools().repositoryUrl("../../scripts/rebuild-docs.js#L1", "reference/commands.md", sha),
    `https://github.com/GPID-WB/compound-gpid/blob/${sha}/scripts/rebuild-docs.js#L1`);
  assert.equal(tools().repositoryUrl("../CONTRIBUTING.md", "installation.md", sha),
    `https://github.com/GPID-WB/compound-gpid/blob/${sha}/CONTRIBUTING.md`);
});

test("source links reject unverified refs, external schemes, escaping paths and private roots", () => {
  for (const ref of [null, undefined, "main", "dev", "a".repeat(39)]) {
    assert.equal(tools().repositoryUrl("../CONTRIBUTING.md", "installation.md", ref), null);
  }
  for (const href of ["../../outside.md", "//evil.test/x", "https://evil.test/x", "javascript:alert(1)",
    "../.git/config", "../secrets/file.md", "../%2e%2e/file.md", "..\\scripts\\a.js", "../scripts//a.js",
    "../scripts/a.js#<script>", "../scripts/a.js?private=value"]) {
    assert.equal(tools().repositoryUrl(href, "installation.md", sha), null, href);
  }
});

test("issue URLs include only page, channel and exact SHA, never search or project data", () => {
  const url = new URL(tools().issueUrl("modular-guide", "development", sha));
  assert.equal(url.origin + url.pathname, "https://github.com/GPID-WB/compound-gpid/issues/new");
  assert.deepEqual([...url.searchParams.keys()], ["title", "body"]);
  assert.equal(url.searchParams.get("body"), `Page: modular-guide\nChannel: development\nSource SHA: ${sha}\n\nDescribe the documentation issue:\n`);
  for (const args of [["x?query=secret", "development", sha], ["guide", "unknown", sha], ["guide", "published", "main"]]) {
    assert.equal(tools().issueUrl(...args), null);
  }
});

test("only explicit loopback or file previews may use a local-preview identity", () => {
  for (const href of ["http://127.0.0.1:8080/compound-gpid/", "http://localhost:3000/dev/", "http://[::1]/", "file:///tmp/docs/index.html"]) {
    assert.equal(tools().isLocalPreview(new URL(href)), true);
  }
  for (const href of ["https://gpid-wb.github.io/compound-gpid/", "https://localhost.evil.test/", "https://example.test/?local=true"]) {
    assert.equal(tools().isLocalPreview(new URL(href)), false);
  }
});

test("copyable code excludes output and prompted or numbered transcripts without rewriting commands", () => {
  for (const [language, text] of [["sh", 'cg-skill inspect "a b"\n  --format json'], ["python", "value_name = 1"], ["", "/cg-work phase1"]]) {
    assert.equal(tools().copyable({ language, text }), true);
  }
  for (const [language, text] of [["output", "Success"], ["console", "$ cg-link\nLinked"], ["text", "Illustrative output"],
    ["sh", "$ cg-link"], ["powershell", "PS C:\\Project> cg-link"], ["python", ">>> example()"], ["sh", "1: cg-link"]]) {
    assert.equal(tools().copyable({ language, text }), false);
  }
});
