/* Reading tools. Publication identity must come from the verified shell contract. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DocsTools = factory();
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";
  const repository = "https://github.com/GPID-WB/compound-gpid";
  const validSha = value => typeof value === "string" && /^[0-9a-f]{40}$/.test(value);

  /** Resolve a relative repository link only with a caller-verified full SHA.
   * Example: repositoryUrl('../CONTRIBUTING.md', 'installation.md', sha).
   */
  function repositoryUrl(href, activeFile, sha) {
    if (!validSha(sha) || typeof href !== "string" || typeof activeFile !== "string"
      || !/^[a-z0-9][a-z0-9./-]*\.md$/.test(activeFile)
      || activeFile.split("/").some(part => !part || part === "." || part === "..")
      || /[\\%?:\s]/.test(href) || href.startsWith("/")) return null;
    const [relative, fragment, extra] = href.split("#");
    if (!relative || extra !== undefined || (fragment !== undefined && !/^[\p{L}\p{N}_-]+$/u.test(fragment))) return null;
    const segments = ["docs", ...activeFile.split("/").slice(0, -1)];
    for (const part of relative.split("/")) {
      if (!part || !/^[A-Za-z0-9_.-]+$/.test(part)) return null;
      if (part === "..") { if (!segments.length) return null; segments.pop(); }
      else if (part !== ".") segments.push(part);
    }
    const file = segments.join("/");
    if (!/^(?:(?:docs|scripts|bin|\.github)\/.+|README\.md|CONTRIBUTING\.md|LICENSE(?:\.md)?|compound-gpid\.md|SCHEMA_VERSION)$/.test(file)) return null;
    return `${repository}/blob/${sha}/${file}${fragment ? `#${encodeURIComponent(fragment)}` : ""}`;
  }

  /** Build a bounded issue template from public page/channel/SHA only; never accept query text. */
  function issueUrl(page, channel, sha) {
    if (!validSha(sha) || typeof page !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(page)
      || !["published", "development"].includes(channel)) return null;
    const query = new URLSearchParams({ title: `Documentation: ${page}`,
      body: `Page: ${page}\nChannel: ${channel}\nSource SHA: ${sha}\n\nDescribe the documentation issue:\n` });
    return `${repository}/issues/new?${query}`;
  }

  /** Local preview is limited to file/loopback URLs, not a query flag on a public host. */
  function isLocalPreview(url) {
    return url.protocol === "file:" || (["http:", "https:"].includes(url.protocol)
      && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname));
  }

  /** Copy command/code bytes unchanged; output and recognizable transcripts are not invocations. */
  function copyable(block) {
    return !/^(?:text|plaintext|output|console|log|terminal)(?:\s|$)/i.test(block.language)
      && !/^\s*(?:\$ |PS [^\n>]*> |>>> |\d+[:|]\s)/m.test(block.text);
  }

  /** Bind accessible copy feedback and manual selection to the freshly rendered article. */
  function mount(article) {
    for (const block of article.querySelectorAll(".code-block")) {
      const button = block.querySelector(".copy-code");
      if (!button) continue;
      const code = block.querySelector("code"), status = block.querySelector("[role=status]"), select = block.querySelector(".select-code");
      button.addEventListener("click", async () => {
        button.disabled = true; status.textContent = ""; select.hidden = true;
        try {
          await navigator.clipboard.writeText(code.textContent);
          status.textContent = "Copied";
        } catch {
          status.textContent = "Copy failed. Select the code and copy it manually."; select.hidden = false;
        } finally { button.disabled = false; }
      });
      select.addEventListener("click", () => {
        const range = document.createRange(); range.selectNodeContents(code);
        const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
        status.textContent = "Code selected. Use your system copy shortcut.";
      });
    }
  }

  /** Show only an unverified identity until step 5 supplies loaded-shell verification. */
  function init() {
    document.querySelector("[data-build-identity]").textContent = isLocalPreview(location)
      ? "Local preview: version unavailable" : "Build identity unavailable (unverified)";
  }

  return { repositoryUrl, issueUrl, isLocalPreview, copyable, mount, init };
});
