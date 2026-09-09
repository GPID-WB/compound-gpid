"use strict";
// Created 2026-09-03.

const test = require("node:test");
const assert = require("node:assert/strict");
const { readFile } = require("node:fs/promises");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const handbookRoot = path.join(root, "docs", "research");
const handbookFiles = {
  index: "index.md",
  philosophy: "philosophy.md",
  firstWorkflow: "first-workflow.md",
  shortExample: "short-example.md",
  lifecycle: "lifecycle.md",
  evidenceBoundaries: "evidence-boundaries.md",
};

async function readHandbookFile(file) {
  return readFile(path.join(handbookRoot, file), "utf8");
}

async function readNavigation() {
  return JSON.parse(await readFile(path.join(root, "docs", "navigation.json"), "utf8"));
}

test("Research Handbook routes are complete and ordered", async () => {
  const navigation = await readNavigation();
  const group = navigation.groups.find((entry) => entry.title === "Research Handbook");
  assert.ok(group, "Research Handbook navigation group is required");
  assert.deepEqual(group.pages.map((page) => page.file), [
    "research/index.md",
    "research/philosophy.md",
    "research/first-workflow.md",
    "research/short-example.md",
    "research/lifecycle.md",
    "research/evidence-boundaries.md",
  ]);
  for (const file of Object.values(handbookFiles)) {
    const content = await readHandbookFile(file);
    assert.match(content, /^#\s+\S/m, `${file} needs a level-one heading`);
    assert.match(content, /Created 2026-09-03/, `${file} needs its creation date`);
  }
});

test("Start Here documents activation, first action, and recovery", async () => {
  const content = await readHandbookFile(handbookFiles.index);
  assert.match(content, /suites: \[cr\]/);
  assert.match(content, /suites: \[cg, cr\]/);
  assert.match(content, /\/cg-setup/);
  assert.match(content, /\/cr-brainstorm/);
  assert.match(content, /If you get stuck/);
  assert.match(content, /missing|unavailable|blocked/i);
});

test("First workflow preserves the complete CR command order", async () => {
  const content = await readHandbookFile(handbookFiles.firstWorkflow);
  const commandOrder = ["/cr-brainstorm", "/cr-plan", "/cr-work", "/cr-review", "/cr-compound"];
  let previous = -1;
  for (const command of commandOrder) {
    const position = content.indexOf(command);
    assert.ok(position > previous, `${command} must follow the previous CR command`);
    previous = position;
  }
  assert.match(content, /What the researcher decides/);
  assert.match(content, /expected result|leaves behind/i);
});

test("Short example contains the approved Kenya task without becoming a tutorial", async () => {
  const content = await readHandbookFile(handbookFiles.shortExample);
  assert.match(content, /-1\.2921/);
  assert.match(content, /36\.8219/);
  assert.match(content, /2020 to present/);
  assert.match(content, /\/cr-brainstorm/);
  assert.match(content, /\/cr-plan/);
  assert.match(content, /\/cr-work/);
  assert.match(content, /\/cr-review/);
  assert.match(content, /\/cr-compound/);
  assert.match(content, /95th percentile/);
  assert.doesNotMatch(content, /\/Users\/|01_fetch_inputs\.R|renv\.lock/);
  assert.ok(content.split("\n").length <= 100, "short example should remain compact");
});

test("Lifecycle and evidence chapters preserve CR boundaries", async () => {
  const lifecycle = await readHandbookFile(handbookFiles.lifecycle);
  const evidence = await readHandbookFile(handbookFiles.evidenceBoundaries);
  for (const taskType of [
    "Research Scoping", "Theory/Modeling", "Specification Analysis", "EDA",
    "Implementation", "ML/Prediction", "Measurement/Classification", "Writing",
    "Tables/Figures", "Reproducibility",
  ]) {
    assert.ok(lifecycle.includes(taskType), `${taskType} is missing`);
  }
  let lifecyclePosition = -1;
  for (const stage of ["Scope", "Evidence", "Theory", "Method", "Execute", "Verify", "Communicate", "Maintain"]) {
    const position = lifecycle.indexOf(`**${stage}**`);
    assert.ok(position > lifecyclePosition, `${stage} must follow the previous lifecycle stage`);
    lifecyclePosition = position;
  }
  assert.match(evidence, /Proof Carrying Claim/);
  assert.match(evidence, /cannot establish by itself|does not establish by itself/);
  assert.match(evidence, /normative choices/);
});
