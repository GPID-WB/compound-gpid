"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const workflow = fs.readFileSync(path.join(root, ".github/workflows/pages.yml"), "utf8");
const validation = fs.readFileSync(path.join(root, ".github/workflows/docs-site-build.yml"), "utf8");

test("every plugin or documentation change on either publication branch triggers a build", () => {
  assert.match(workflow, /push:\s*\n\s*branches:\s*\[main, dev\]/);
  assert.doesNotMatch(workflow, /paths(?:-ignore)?:/);
  assert.match(workflow, /workflow_dispatch:/);
  assert.match(workflow, /if: github.ref == 'refs\/heads\/dev' \|\| github.ref == 'refs\/heads\/main'/);
});

test("rendering stays read-only and deployment receives only the built artifact", () => {
  const [build, deploy] = workflow.split("  deploy:");
  assert.match(build, /ref: \$\{\{ github.sha \}\}/);
  assert.match(build, /persist-credentials: false/);
  assert.match(build, /rebuild-docs.js --root sources\/main --all/);
  assert.match(build, /rebuild-docs.js --root sources\/dev --all/);
  assert.match(build, /assemble-docs-site.js/);
  assert.match(build, /check-rendered-docs.js/);
  assert.match(build, /path: combined-artifact\/site/);
  assert.doesNotMatch(build, /(?:pages|id-token|contents):\s*write|actions\/deploy-pages/);
  assert.match(deploy, /needs: build/);
  assert.match(deploy, /pages: write/);
  assert.match(deploy, /actions\/deploy-pages/);
  assert.doesNotMatch(deploy, /actions\/checkout|node scripts|contents:\s*write/);
  assert.match(deploy, /commits\/main/);
  assert.match(deploy, /commits\/dev/);
  assert.match(deploy, /\$MAIN_SHA/);
  assert.match(deploy, /\$DEV_SHA/);
});

test("PRs render and validate a review artifact without publication permissions", () => {
  assert.match(validation, /pull_request:\s*\n\s*branches: \[main, dev\]/);
  assert.doesNotMatch(validation, /pull_request_target|workflow_run|(?:pages|id-token|contents):\s*write/);
  for (const command of ["npm run docs:build", "npm run docs:test", "npm run docs:render", "node scripts/check-rendered-docs.js .site"]) assert.ok(validation.includes(command), command);
  assert.match(validation, /path: .site\//);
  assert.doesNotMatch(validation, /actions\/deploy-pages|git push|legacy-pages/);
});
