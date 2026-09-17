"use strict";
const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./scripts/tests",
  testMatch: "docs-browser.spec.js",
  outputDir: "./test-results/docs-browser",
  timeout: 30000,
  expect: { timeout: 5000 },
  workers: 1,
  retries: 0,
  use: { browserName: "chromium", trace: "retain-on-failure", screenshot: "only-on-failure" },
});
