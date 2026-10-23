"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const producer = fs.readFileSync(path.join(root, ".github/workflows/pages.yml"), "utf8");
const validation = fs.readFileSync(path.join(root, ".github/workflows/docs-site-build.yml"), "utf8");

test("every dev commit can refresh documentation, including newly introduced source paths", () => {
  assert.match(producer, /push:\s*\n\s*branches:\s*\[dev\]/);
  assert.doesNotMatch(producer, /paths(?:-ignore)?:/);
  assert.match(producer, /workflow_dispatch:/);
  assert.match(producer, /if: github.ref == 'refs\/heads\/dev'/);
});

test("development publication hands the exact generated tree to the existing protected controller", () => {
  assert.match(producer, /^name: Deploy documentation site$/m);
  assert.match(producer, /ref: \$\{\{ github.sha \}\}/);
  assert.match(producer, /persist-credentials: false/);
  assert.match(producer, /node scripts\/rebuild-docs.js --all\s+node scripts\/check-docs-site.js/);
  assert.match(producer, /name: legacy-dev-docs/);
  assert.match(producer, /docs\/\s+\.docs-build-metadata.json/);
  assert.match(producer, /include-hidden-files: true/);
  assert.doesNotMatch(producer, /(?:pages|id-token|contents):\s*write|actions\/deploy-pages/);
});

test("pull requests validate and test documentation without publishing or modifying branches", () => {
  assert.match(validation, /pull_request:\s*\n\s*branches: \[main, dev\]/);
  assert.doesNotMatch(validation, /pull_request_target|workflow_run|(?:pages|id-token|contents):\s*write/);
  assert.match(validation, /npm run docs:build/);
  assert.match(validation, /npm run docs:test/);
  assert.match(validation, /actions\/upload-artifact@/);
  assert.match(validation, /legacy-pages.js import-dev/);
  assert.match(validation, /ref: main/);
  assert.doesNotMatch(validation, /actions\/deploy-pages|git push/);
});
