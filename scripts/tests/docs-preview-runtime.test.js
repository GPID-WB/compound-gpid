"use strict";
// Created 2026-09-03.

const test = require("node:test");
const assert = require("node:assert/strict");
const { createServer } = require("node:http");
const { spawnSync } = require("node:child_process");
const { mkdtemp, readFile, rm } = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const assembler = path.join(root, "scripts", "assemble-docs-site.js");
const node = process.execPath;

function startStaticServer(siteRoot) {
  const server = createServer(async (request, response) => {
    try {
      const requested = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
      const relative = requested.endsWith("/") ? `${requested}index.html` : requested;
      const target = path.resolve(siteRoot, `.${relative}`);
      if (!target.startsWith(`${path.resolve(siteRoot)}${path.sep}`)) {
        response.writeHead(400);
        response.end("unsafe path");
        return;
      }
      const content = await readFile(target);
      response.writeHead(200);
      response.end(content);
    } catch {
      response.writeHead(404);
      response.end("not found");
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => {
    const address = server.address();
    resolve({ server, baseUrl: `http://127.0.0.1:${address.port}` });
  }));
}

test("stable root and /dev/ preview serve the same site shell at distinct paths", async () => {
  const output = await mkdtemp(path.join(os.tmpdir(), "cg-preview-runtime-"));
  try {
    const built = spawnSync(node, [
      assembler,
      "--main-root", root,
      "--dev-root", root,
      "--out", output,
      "--main-sha", "1111111111111111111111111111111111111111",
      "--dev-sha", "2222222222222222222222222222222222222222",
    ], { encoding: "utf8" });
    assert.equal(built.status, 0, built.stderr + built.stdout);
    const { server, baseUrl } = await startStaticServer(path.join(output, "site"));
    try {
      for (const relative of [
        "/",
        "/navigation.json",
        "/assets/site.css",
        "/assets/site.js",
        "/dev/",
        "/dev/navigation.json",
        "/dev/assets/site.css",
        "/dev/assets/site.js",
        "/dev/research/index.md",
      ]) {
        const response = await fetch(`${baseUrl}${relative}`);
        assert.equal(response.status, 200, relative);
      }
      const stableIndex = await (await fetch(`${baseUrl}/`)).text();
      const devIndex = await (await fetch(`${baseUrl}/dev/`)).text();
      const devScript = await (await fetch(`${baseUrl}/dev/assets/site.js`)).text();
      assert.doesNotMatch(stableIndex, /dev-preview-banner/);
      assert.match(devIndex, /dev-preview-banner/);
      assert.match(devIndex, /Development preview built from/);
      assert.match(devScript, /fetch\("navigation\.json"\)/);
      assert.match(devScript, /fetch\(config\.file\)/);
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  } finally {
    await rm(output, { recursive: true, force: true });
  }
});
