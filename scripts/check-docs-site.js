const { access, readFile } = require("node:fs/promises");
const { constants } = require("node:fs");

(async () => {
  const requiredFiles = ["docs/index.html", "docs/assets/site.css", "docs/assets/site.js", "docs/.nojekyll"];
  const workflow = await readFile(".github/workflows/pages.yml", "utf8");
  const siteScript = await readFile("docs/assets/site.js", "utf8");
  const pageFiles = [...siteScript.matchAll(/"([a-z-]+\.md)"/g)].map((match) => `docs/${match[1]}`);

  for (const file of [...requiredFiles, ...pageFiles]) await access(file, constants.R_OK);

  for (const action of ["actions/configure-pages", "actions/upload-pages-artifact", "actions/deploy-pages"]) {
    if (!workflow.includes(action)) throw new Error(`Pages workflow must use ${action}.`);
  }

  if (!workflow.includes("path: docs")) throw new Error("Pages workflow must upload the docs directory.");
  if (!siteScript.includes("navigationRequest")) throw new Error("Site router must guard against stale page loads.");

  console.log(`Documentation site check passed (${pageFiles.length} canonical Markdown pages).`);
})();
