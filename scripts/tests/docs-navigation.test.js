"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "../..");
const contract = () => require("../../docs/assets/docs-contract.js");
const workflow = fs.readFileSync(path.join(root, ".github/workflows/tests.yml"), "utf8").replace(/\r\n/g, "\n");
const browserJob = workflow.match(/^  browser-evidence:\n[\s\S]*?(?=^  \S)/m)[0];
const browserSteps = browserJob.split(/(?=^      - )/m).slice(1);

// Inspect one registered step, not a matching command in a comment or another job.
function workflowStep(name) {
  const step = browserSteps.find(value => value.startsWith(`      - name: ${name}\n`));
  assert.ok(step, `Missing browser-evidence step: ${name}`);
  return step;
}

function render(markdown, script = "docs/assets/site.js") {
  const context = vm.createContext({
    document: { querySelector: () => ({}) },
    DocsContract: fs.existsSync(path.join(root, "docs/assets/docs-contract.js")) ? contract() : undefined,
    URLSearchParams, location: { hash: "" },
  });
  const source = fs.readFileSync(path.join(root, script), "utf8");
  vm.runInContext(source.slice(0, source.indexOf('document.querySelectorAll("[data-open-search]")')), context);
  return vm.runInContext(`markdownToHtml(${JSON.stringify(markdown)})`, context);
}

const page = (id, extra = {}) => ({ id, title: id, file: `${id}.md`, description: id, ...extra });
const manifest = (...pages) => ({ schemaVersion: "compound-gpid-docs-navigation-v1", groups: [{ title: "Guide", pages }] });

test("renderer assigns unique deterministic heading IDs, including literal suffix collisions", () => {
  const html = render("# Title\n## Repeat\n## Repeat\n## Repeat-1\n## Repeat");
  assert.deepEqual([...html.matchAll(/<h\d id="([^"]+)"/g)].map(m => m[1]),
    ["title", "repeat", "repeat-1", "repeat-1-1", "repeat-2"]);
});

test("shared headings handle punctuation, links, inline code, Unicode, and empty slugs", () => {
  const rows = contract().extractHeadings("# API: `a_b()` / [Guide](guide.md)\n## Caf\u00e9 \u4e2d\u6587\n## !!!");
  assert.deepEqual(rows.map(row => row.id), ["api-ab-guide", "caf\u00e9-\u4e2d\u6587", "section"]);
  assert.equal(rows[0].level, 1);
  assert.equal(rows[0].line, 0);
});

test("headings exclude frontmatter, comments, and both fence forms, including longer fences", () => {
  const markdown = "---\ntitle: x\n---\n# Visible\n````md\n# Hidden\n```\n## Still hidden\n````\n  ~~~\n# Also hidden\n  ~~~\n<!--\n# Comment\n-->\n## End";
  assert.deepEqual(contract().extractHeadings(markdown).map(row => row.id), ["visible", "end"]);
  assert.deepEqual([...render(markdown).matchAll(/<h\d id="([^"]+)"/g)].map(m => m[1]), ["visible", "end"]);
});

test("nested list and quote headings share the article heading namespace", () => {
  const markdown = "# Title\n> ## Repeat\n\n- Item\n  ## Repeat\n\n## Repeat";
  const ids = [...render(markdown).matchAll(/<h\d id="([^"]+)"/g)].map(m => m[1]);
  assert.deepEqual(ids, contract().extractHeadings(markdown).map(row => row.id));
  assert.deepEqual(ids, ["title", "repeat", "repeat-1", "repeat-2"]);
});

test("legacy aliases resolve only when unambiguous and never override canonical IDs", () => {
  const headings = contract().extractHeadings("# A/B\n## AB\n## Again\n## Again");
  const aliases = contract().headingAliases(headings);
  assert.ok(aliases.ambiguous.includes("ab"));
  assert.ok(aliases.ambiguous.includes("again"));
  assert.equal(aliases.aliases.ab, undefined);
  assert.equal(contract().resolveSection(headings, "ab").status, "ambiguous");
  assert.equal(contract().resolveSection(headings, "again-1").id, "again-1");
  assert.equal(contract().resolveSection(contract().extractHeadings("# One/Two"), "onetwo").id, "one-two");
});

test("manifest keeps old records visible and hidden references registered and searchable", () => {
  const result = contract().validateManifest(manifest(page("guide"), page("ref", { sidebar: false })));
  assert.equal(result.length, 2);
  assert.equal(contract().sidebarVisible(result[0]), true);
  assert.equal(contract().sidebarVisible(result[1]), false);
  assert.equal(contract().searchable(result[1]), true);
});

test("redirects validate page/section targets, mappings, defaults, and compatibility search exclusion", () => {
  const pages = contract().validateManifest(manifest(page("guide"), page("old", {
    sidebar: false, redirect: { page: "guide", section: "start", sections: { prior: "details" } },
  })), { guide: contract().extractHeadings("# Guide\n## Start\n## Details"), old: contract().extractHeadings("# Old\n## Prior") });
  assert.equal(contract().searchable(pages[1]), false);
  assert.deepEqual(contract().resolveRoute(pages, "old", "prior"), { page: "guide", section: "details" });
  assert.deepEqual(contract().resolveRoute(pages, "old", null), { page: "guide", section: "start" });
  assert.deepEqual(contract().resolveRoute(pages, "old", "unknown"), { page: "guide", section: "unknown" });
});

for (const [name, make] of [
  ["duplicate IDs", () => manifest(page("same"), page("same", { file: "other.md" }))],
  ["duplicate files", () => manifest(page("a"), page("b", { file: "a.md" }))],
  ["unsafe paths", () => manifest(page("a", { file: "../secret.md" }))],
  ["encoded traversal", () => manifest(page("a", { file: "%2e%2e/secret.md" }))],
  ["empty path segments", () => manifest(page("a", { file: "a//b.md" }))],
  ["reserved home ID", () => manifest(page("home"))],
  ["non-string IDs", () => manifest(page(123))],
  ["visibility type", () => manifest(page("a", { sidebar: "false" }))],
  ["missing redirect target", () => manifest(page("old", { redirect: { page: "absent", sections: {} } }))],
  ["redirect cycles", () => manifest(page("a", { redirect: { page: "b", sections: {} } }), page("b", { redirect: { page: "a", sections: {} } }))],
  ["unsafe section", () => manifest(page("a"), page("b", { redirect: { page: "a", section: "<script>", sections: {} } }))],
]) {
  test(`rejects manifest ${name}`, () => {
    const { validateManifest } = contract();
    assert.throws(() => validateManifest(make()), /Documentation navigation/);
  });
}

test("missing mapped headings fail content-aware manifest validation", () => {
  assert.throws(() => contract().validateManifest(manifest(page("a"), page("old", {
    redirect: { page: "a", sections: { prior: "missing" } },
  })), { a: contract().extractHeadings("# A"), old: contract().extractHeadings("# Old\n## Prior") }), /missing.*section/i);
});

test("continuing CI selects the complete bounded docs Node test inventory", () => {
  const selected = JSON.parse(fs.readFileSync(path.join(root, "package.json"))).scripts["test:docs-automation"].split(/\s+/).slice(2).sort();
  const expected = fs.readdirSync(path.join(root, "scripts/tests"))
    .filter(name => /^(?:docs-.*|.*-docs(?:-.*)?|generate-whats-new|release-version|legacy-pages)\.test\.js$/.test(name))
    .map(name => `scripts/tests/${name}`).concat("scripts/evidence/tests/release-pages.test.js").sort();
  assert.deepEqual(selected, expected);
  assert.match(workflowStep("Run documentation automation tests"), /^        run: npm run test:docs-automation$/m);
  const ordered = ["Run documentation automation tests", "Install Chromium for evidence capture",
    "Run documentation browser tests", "Capture browser evidence manifest", "Run browser evidence tests"];
  const positions = ordered.map(name => browserJob.indexOf(workflowStep(name)));
  assert.deepEqual(positions, [...positions].sort((a, b) => a - b));
});

test("CI recovery repairs the lockfile only on explicit boolean dispatch opt-in", () => {
  const dispatch = workflow.match(/^  workflow_dispatch:\n[\s\S]*?(?=^\S)/m)[0];
  assert.match(dispatch, /^      repair_docs_lockfile:\n        description: .+\n        type: boolean\n        required: false\n        default: false$/m);
  assert.equal((dispatch.match(/^      \w+:/gm) || []).length, 1);
  const repair = workflowStep("Repair docs lockfile (explicit dispatch only)");
  assert.match(repair, /^        if: github.event_name == 'workflow_dispatch' && inputs.repair_docs_lockfile == true$/m);
  assert.match(repair, /^        run: npm install --package-lock-only --ignore-scripts --no-audit --no-fund$/m);
  const install = workflowStep("Install Node test dependencies");
  assert.match(install, /^        run: npm ci --ignore-scripts --no-audit --no-fund$/m);
  assert.doesNotMatch(install, /^        if:|npm install|\|\|/m);
  assert.ok(browserJob.indexOf(repair) < browserJob.indexOf(install));
  assert.ok(browserJob.indexOf(install) < browserJob.indexOf(workflowStep("Run documentation automation tests")));
  assert.equal(browserSteps.filter(step => /^        run:.*npm install/m.test(step)).length, 1);
});

test("CI recovery binds checkout and always uploads bounded browser diagnostics without masking failure", () => {
  const checkout = browserSteps.find(step => step.includes("uses: actions/checkout@"));
  assert.match(checkout, /^          ref: \$\{\{ github.sha \}\}$/m);
  assert.match(checkout, /^          persist-credentials: false$/m);
  assert.match(checkout, /^          fetch-depth: 0$/m);
  assert.match(browserJob, /^    permissions:\n      contents: read\n    steps:/m);
  assert.doesNotMatch(browserJob, /continue-on-error|\|\| true|exit 0/);
  const browser = workflowStep("Run documentation browser tests");
  assert.match(browser, /^        run: npm run test:docs-browser -- --reporter=line,json$/m);
  assert.match(browser, /^          PLAYWRIGHT_JSON_OUTPUT_NAME: test-results\/docs-browser.json$/m);
  for (const name of ["Run documentation automation tests", "Install Chromium for evidence capture",
    "Run documentation browser tests", "Capture browser evidence manifest", "Run browser evidence tests"]) {
    assert.doesNotMatch(workflowStep(name), /^        if:|--grep|--pass-with-no-tests|--max-failures/m);
  }
  assert.match(workflowStep("Capture browser evidence manifest"), /^        run: npm run capture$/m);
  assert.match(workflowStep("Run browser evidence tests"), /^        run: npm test$/m);
  const config = fs.readFileSync(path.join(root, "playwright.docs.config.js"), "utf8");
  assert.match(config, /testMatch: "docs-browser.spec.js"/);
  assert.match(config, /trace: "retain-on-failure", screenshot: "only-on-failure"/);
  assert.match(config, /retries: 0/);
  const upload = workflowStep("Upload docs browser recovery evidence");
  assert.match(upload, /^        if: always\(\)$/m);
  assert.match(upload, /uses: actions\/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02/);
  assert.match(upload, /^          name: docs-browser-evidence-\$\{\{ github.run_id \}\}-\$\{\{ github.run_attempt \}\}$/m);
  assert.match(upload, /^          retention-days: 7$/m);
  assert.match(upload, /^          if-no-files-found: error$/m);
  assert.deepEqual(upload.match(/^          path: \|\n((?:            .+\n)+)/m)[1].trim().split(/\n\s*/), [
    "package.json", "package-lock.json", "test-results/docs-browser.json",
    "test-results/docs-browser/", "test-results/docs-browser-provenance.json",
  ]);
  assert.ok(browserJob.indexOf(upload) > browserJob.indexOf(workflowStep("Record docs browser provenance")));
});

test("CI recovery provenance records source, run, lock digest, versions and failed or skipped outcomes", () => {
  const metadata = workflowStep("Record docs browser provenance");
  assert.match(metadata, /^        if: always\(\)$/m);
  assert.match(metadata, /^          STEP_RESULTS: \$\{\{ toJSON\(steps\) \}\}$/m);
  assert.match(metadata, /^          REPAIR_REQUESTED: \$\{\{ github.event_name == 'workflow_dispatch' && inputs.repair_docs_lockfile == true \}\}$/m);
  const source = metadata.match(/          node <<'NODE'\n([\s\S]*?)          NODE\n/)[1].replace(/^          /gm, "");
  const sha = "a".repeat(40), hash = value => require("node:crypto").createHash("sha256").update(value).digest("hex");
  const pins = JSON.parse(fs.readFileSync(path.join(root, "package.json"))).devDependencies;
  const steps = Object.fromEntries(["checkout", "node", "repair", "dependencies", "docs_automation", "chromium",
    "docs_browser", "capture", "evidence_tests"].map(id => [id, { outcome: "success", conclusion: "success" }]));
  const files = { "package.json": JSON.stringify({ devDependencies: pins }), "package-lock.json": "repaired-lock",
    "test-results/docs-browser.json": "{\"stats\":{\"unexpected\":1}}" };
  for (const [name, version] of Object.entries(pins)) files[`node_modules/${name}/package.json`] = JSON.stringify({ version });
  let written;
  const context = vm.createContext({
    process: { version: "v22.0.0", env: { GITHUB_REPOSITORY: "GPID-WB/compound-gpid", GITHUB_EVENT_NAME: "workflow_dispatch",
      GITHUB_REF: "refs/heads/improve-website-design", GITHUB_SHA: sha, GITHUB_RUN_ID: "123", GITHUB_RUN_ATTEMPT: "2",
      REPAIR_REQUESTED: "true", STEP_RESULTS: JSON.stringify({ ...steps,
        docs_browser: { outcome: "failure", conclusion: "failure" }, capture: { outcome: "skipped", conclusion: "skipped" } }) } },
    require: name => {
      if (name === "node:fs") return {
        readFileSync: file => { assert.ok(Object.hasOwn(files, file), file); return Buffer.from(files[file]); },
        mkdirSync: () => {}, writeFileSync: (file, text) => { assert.equal(file, "test-results/docs-browser-provenance.json"); written = JSON.parse(text); },
      };
      if (name === "node:child_process") return { execFileSync: (command, args) => {
        if (command === "git" && args.join(" ") === "rev-parse HEAD") return sha;
        if (command === "git" && args.join(" ") === "show HEAD:package-lock.json") return "checked-in-lock";
        if (command === "npm" && args.join(" ") === "--version") return "10.0.0";
        throw new Error("Browser not installed");
      } };
      if (name === "playwright") throw new Error("Browser not installed");
      assert.equal(name, "node:crypto"); return require(name);
    },
  });
  vm.runInContext(source, context);
  assert.equal(written.checkedOutSha, sha); assert.equal(written.eventSha, sha);
  assert.equal(written.repository, "GPID-WB/compound-gpid");
  assert.equal(written.runId, "123"); assert.equal(written.runAttempt, "2");
  assert.equal(written.repairRequested, true);
  assert.equal(written.packageJsonSha256, hash(files["package.json"]));
  assert.equal(written.lockfileSha256, hash("repaired-lock"));
  assert.equal(written.checkedInLockfileSha256, hash("checked-in-lock"));
  assert.equal(written.browserResultsSha256, hash(files["test-results/docs-browser.json"]));
  assert.equal(written.versions.node, "v22.0.0"); assert.equal(written.versions.npm, "10.0.0");
  assert.deepEqual(written.versions.packages, pins); assert.equal(written.versions.chromium, null);
  assert.equal(written.steps.docs_browser.outcome, "failure"); assert.equal(written.steps.capture.outcome, "skipped");
  for (const [id, command] of Object.entries(written.commands)) {
    const step = browserSteps.find(value => value.includes(`        id: ${id}\n`));
    assert.ok(step?.includes(`        run: ${command}\n`), `Recorded command must match executed step ${id}`);
  }
  assert.equal(Object.keys(written.commands).length, 7);
  context.process.env.REPAIR_REQUESTED = "false";
  context.process.env.STEP_RESULTS = JSON.stringify({ ...steps, repair: { outcome: "skipped", conclusion: "skipped" } });
  delete files["test-results/docs-browser.json"];
  assert.throws(() => vm.runInContext(`{${source}}`, context), /Browser results missing/);
  assert.equal(written.repairRequested, false);
  context.process.env.GITHUB_SHA = "b".repeat(40);
  assert.throws(() => vm.runInContext(`{${source}}`, context), /Checkout SHA does not match/);
});
