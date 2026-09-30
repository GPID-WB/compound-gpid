/* Loaded-shell verification and channel switching. No producer code executes in the browser. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DocsIdentity = factory();
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";
  const digestPattern = /^[a-f0-9]{64}$/;
  const pathPattern = /^(?:\.nojekyll|[A-Za-z0-9_-][A-Za-z0-9_./-]*)$/;
  const safePath = value => typeof value === "string" && pathPattern.test(value) && value.split("/").every(p => p && p !== "." && p !== "..");
  const fail = message => { const error = Error(message); error.buildChanged = true; throw error; };
  let metadata, active, channelName, base, local, locked = false, ready = false;

  /** Validate bounded channel identities and digests before using any data or destination. */
  function validate(value) {
    if (value?.schemaVersion !== "compound-gpid-docs-channels-v1" || !value.channels ||
      Object.keys(value.channels).sort().join() !== "development,published") fail("Invalid channel metadata");
    for (const [name, c] of Object.entries(value.channels)) {
      const v = c.fingerprintVersion;
      if (![1, 2].includes(v) || c.producerContract !== `compound-gpid-docs-producer-v${v}` ||
        c.runtimeContract !== `compound-gpid-docs-runtime-v${v}` || c.headingContract !== `compound-gpid-headings-v${v}` ||
        c.path !== (name === "published" ? "" : "dev/") || !/^[a-f0-9]{40}$/.test(c.source?.sha) ||
        ![c.source?.branch, c.source?.ref].every(s => typeof s === "string" && /^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(s) && !s.includes("..")) ||
        !digestPattern.test(c.fingerprint) || !c.files || typeof c.files !== "object" || Array.isArray(c.files) ||
        Object.keys(c.files).length > 10000 || !Object.entries(c.files).every(([p, h]) => safePath(p) && !p.startsWith("dev/") && p !== "channels.json" && digestPattern.test(h))) fail("Unsupported channel identity");
      if (name === "development" && (c.source.branch !== "dev" || c.source.ref !== "dev" || c.source.tag)) fail("Invalid dev identity");
      if (c.source.tag && (!/^v\d+\.\d+\.\d+(?:\.\d+)?$/.test(c.source.tag) || c.source.tag !== c.source.ref)) fail("Invalid release identity");
      const expected = { sectionLinks: true, redirectMappings: v === 2, switchNotices: v === 2, reverseSwitching: v === 2, verifiedIdentity: v === 2 };
      if (JSON.stringify(Object.keys(c.capabilities || {}).sort()) !== JSON.stringify(Object.keys(expected).sort()) ||
        Object.entries(expected).some(([key, val]) => c.capabilities[key] !== val)) fail("Unknown channel capabilities");
      if (!Array.isArray(c.assets) || (v === 1 ? c.shellBuildId !== null || c.assets.length : !digestPattern.test(c.shellBuildId) || c.assets.length !== 7)) fail("Invalid shell identity");
    }
    return value;
  }

  async function digest(bytes) {
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(n => n.toString(16).padStart(2, "0")).join("");
  }
  async function readJson(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) fail("Build metadata unavailable");
    const value = validate(await response.json());
    for (const c of Object.values(value.channels)) {
      if (c.fingerprintVersion !== 2) continue;
      const bytes = new TextEncoder().encode(JSON.stringify([c.source.sha, c.fingerprint, c.producerContract,
        c.fingerprintVersion, c.runtimeContract, c.headingContract]));
      if (await digest(bytes) !== c.shellBuildId) fail("Channel shell identity mismatch");
    }
    return value;
  }
  function notice(text) {
    const node = document.querySelector("[data-build-notice]"); node.hidden = false; node.textContent = text;
    document.querySelector("[data-build-reload]").hidden = false;
  }
  function changed(error) {
    locked = true;
    notice("The documentation build changed or could not be verified. Reload the full page to continue. " + error.message);
    document.querySelector("[data-channel-switch]").disabled = true;
    error.buildChanged = true; return error;
  }

  /** Fetch only bytes declared by the selected channel; never downgrade to an unverified response. */
  async function verifiedText(file, destination = active) {
    if (locked || !safePath(file) || !destination.files[file]) fail("Unverified documentation file");
    const response = await fetch(new URL(destination.path + file, base), { cache: "no-store" });
    if (!response.ok) fail("Documentation file unavailable");
    const bytes = await response.arrayBuffer();
    if (await digest(bytes) !== destination.files[file]) fail("Documentation digest mismatch");
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  }

  /** Recheck metadata on data access so an open tab cannot silently mix deployments. */
  async function read(file) {
    if (!active) {
      if (!local) fail("Build identity unavailable");
      const response = await fetch(file);
      if (!response.ok) throw Error("Documentation unavailable");
      return response.text();
    }
    try {
      await assertCurrent();
      const text = await verifiedText(file);
      if (file.endsWith(".md")) document.querySelector("[data-build-identity]").textContent = label();
      return text;
    } catch (error) { throw changed(error); }
  }

  /** Cached search/data may be reused only while their original channel identity remains current. */
  async function assertCurrent() {
    if (local) return;
    try {
      if (!active || locked || JSON.stringify(await readJson(new URL("channels.json", base))) !== JSON.stringify(metadata)) fail("Channel manifest changed");
    } catch (error) { throw changed(error); }
  }

  function label() {
    if (!active || !ready || locked) return document.querySelector("[data-build-identity]").textContent;
    const release = active.source.tag;
    return `${channelName === "published" ? "Published" : "Development"}: ${release || `${active.source.ref}@${active.source.sha.slice(0, 8)}`}${release?.split(".").length === 4 ? " (prerelease)" : ""}`;
  }

  /** Match the actual DOM stamp, executing runtime stamp and integrity-bearing local assets. */
  async function init(runtimeId) {
    const htmlId = document.querySelector('meta[name="cg-docs-shell"]')?.content;
    local = DocsTools.isLocalPreview(location) && htmlId === "__CG_DOCS_SHELL_BUILD_ID__" && runtimeId === htmlId;
    document.querySelector("[data-build-reload]").addEventListener("click", () => location.reload());
    if (local) return null;
    document.querySelector("[data-build-identity]").textContent = "Build identity unavailable (unverified)";
    try {
      if (!crypto.subtle || !digestPattern.test(htmlId) || runtimeId !== htmlId) fail("Loaded HTML/runtime identity mismatch");
      const directory = new URL(".", location.href);
      channelName = directory.pathname.endsWith("/dev/") ? "development" : "published";
      base = channelName === "development" ? new URL("../", directory) : directory;
      metadata = await readJson(new URL("channels.json", base)); active = metadata.channels[channelName];
      if (active.runtimeContract !== "compound-gpid-docs-runtime-v2" || active.shellBuildId !== htmlId) fail("Loaded shell is stale");
      const seen = new Set();
      for (const asset of active.assets) {
        const expectedPath = asset.source?.replace(/\.(js|css)$/, `.${asset.sha256}.$1`);
        if (!safePath(asset.path) || !digestPattern.test(asset.sha256) || expectedPath !== asset.path ||
          active.files[asset.path] !== asset.sha256 || seen.has(asset.source)) fail("Invalid asset inventory");
        seen.add(asset.source);
        const element = [...document.querySelectorAll("script[src],link[rel=stylesheet]")]
          .find(n => (n.getAttribute("src") || n.getAttribute("href")) === asset.path);
        const integrity = `sha256-${btoa(String.fromCharCode(...asset.sha256.match(/../g).map(h => parseInt(h, 16))))}`;
        if (!element || element.integrity !== integrity || asset.integrity !== integrity ||
          (element.tagName === "LINK" && !element.sheet)) fail("A required shell asset failed integrity loading");
        await verifiedText(asset.path);
      }
      const required = ["site.js", "site.css", "docs-contract.js", "docs-reading.js", "docs-search.js", "docs-tools.js", "docs-identity.js"];
      if (required.some(n => !seen.has(`assets/${n}`))) fail("Missing shell asset");
      if (["DocsContract", "DocsReading", "DocsSearch", "DocsTools", "DocsIdentity"].some(name => !globalThis[name])) fail("A required helper did not execute");
      const select = document.querySelector("[data-channel-switch]"); select.value = channelName; select.disabled = false;
      select.addEventListener("change", () => switchChannel(select.value).catch(error => changed(error)));
      // Reading the first verified article reveals identity; initialization alone does not.
      await read("navigation.json");
      ready = true;
      const query = new URLSearchParams(location.search), message = {
        "page-missing": "The requested page is unavailable in this channel. Showing the documentation homepage.",
        "section-missing": "The requested section is unavailable in this channel. Showing the page from the top.",
      }[query.get("docs-notice")];
      if (message) {
        const node = document.querySelector("[data-channel-notice]"); node.textContent = message; node.hidden = false;
        try {
          const back = new URL(query.get("return"));
          if (back.origin === base.origin && [base.pathname, base.pathname + "dev/"].includes(back.pathname)) {
            const link = document.createElement("a"); link.href = back.href; link.textContent = " Return to the previous channel."; node.append(link);
          }
        } catch { /* A missing/invalid return URL never becomes a link. */ }
      }
      return { ...active.source, channel: channelName };
    } catch (error) { active = null; throw changed(error); }
  }

  /** Switch using destination-specific heading rules, with explicit legacy/fallback confirmation. */
  async function switchChannel(name) {
    if (!active || locked || !["published", "development"].includes(name) || name === channelName) return;
    if (JSON.stringify(await readJson(new URL("channels.json", base))) !== JSON.stringify(metadata)) fail("Channel manifest changed");
    const destination = metadata.channels[name], manifest = JSON.parse(await verifiedText("navigation.json", destination));
    const params = new URLSearchParams(location.hash.slice(1)), pages = DocsContract.validateManifest(manifest);
    let page = params.get("page"), section = params.get("section"), reason = "", fallback;
    if (destination.fingerprintVersion === 2) ({ page, section } = DocsContract.resolveRoute(pages, page, section));
    const config = pages.find(p => p.id === page);
    if (page && !config) { page = null; section = null; fallback = "page-missing"; reason = "This page is unavailable in the destination. The documentation homepage will open."; }
    if (config && section) {
      const markdown = await verifiedText(config.file, destination);
      const headings = destination.headingContract === "compound-gpid-headings-v2" ? DocsContract.parseDocument(markdown).headings.map(h => h.id)
        : legacyHeadings(markdown);
      if (!headings.includes(section)) { section = null; fallback = "section-missing"; reason = "This section is unavailable in the destination. The page will open at the top."; }
    }
    const target = new URL(destination.path, base);
    target.hash = page ? `page=${encodeURIComponent(page)}${section ? `&section=${encodeURIComponent(section)}` : ""}` : "home";
    if (fallback && destination.fingerprintVersion === 2) { target.searchParams.set("docs-notice", fallback); target.searchParams.set("return", location.href); }
    if (destination.fingerprintVersion === 1) reason += " This legacy channel has no verified in-page identity, switch notice, or reverse switch. Use Back or the return URL.";
    if (!reason) { location.assign(target.href); return; }
    const dialog = document.querySelector("[data-channel-dialog]");
    dialog.querySelector("[data-channel-message]").textContent = reason;
    const link = dialog.querySelector("[data-channel-confirm]"); link.href = target.href; link.textContent = `Continue to ${target.href}`;
    const back = dialog.querySelector("[data-channel-return]"); back.value = location.href;
    dialog.querySelector("[data-channel-cancel]").onclick = () => dialog.close();
    dialog.onclose = () => { const select = document.querySelector("[data-channel-switch]"); select.value = channelName; select.focus(); };
    dialog.showModal();
  }

  /** Exact legacy parser heading subset: fence handling and legacy slug bytes. */
  function legacyHeadings(markdown) {
    let fenced = false, comment = false;
    return markdown.replace(/^\uFEFF/, "").replace(/^---[\s\S]*?---\s*/, "").split("\n").flatMap(line => {
      if (!fenced && (comment || line.trim().startsWith("<!--"))) { comment = !line.includes("-->"); return []; }
      if (line.startsWith("```")) { fenced = !fenced; return []; }
      if (fenced) return [];
      const heading = /^(#{1,6})\s+(.+)$/.exec(line);
      return heading ? [heading[2].toLowerCase().replace(/<[^>]*>/g, "").replace(/[`*_]/g, "")
        .replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")] : [];
    });
  }
  return { validate, init, read, assertCurrent, label, legacyHeadings };
});
