# Keep the Documentation Current

Edit the documentation in the repository. GitHub Actions rebuilds the
reference content, renders the website and search index, validates them, and
publishes to GitHub Pages. A Sites preview is a design-review snapshot of the
same build, not the maintained publication pipeline.

## Which website should I use?

| Channel | Address | Source |
|---|---|---|
| Development | [Development handbook](https://gpid-wb.github.io/compound-gpid/dev/) | Latest successfully built `dev` commit |
| Stable | [Stable handbook](https://gpid-wb.github.io/compound-gpid/) | `main`, with release publication also producing a tagged snapshot |

The new pipeline runs on **every push to `dev` and `main`**, without path
filters. Each run builds both channels together. Development work updates
`/dev/`; it does not copy unreleased guides into the stable channel. A
main-branch trigger becomes active when this workflow reaches `main`.

The channel label, source links, and build commit identify what you are reading.
An older stable release can retain its previous site layout until the redesign
is promoted to `main`.

## Merge order: development first, then stable

1. Merge the documentation PR into **`dev`**. GitHub Actions renders and
   deploys the updated [development website](https://gpid-wb.github.io/compound-gpid/dev/).
   A merge into `main` is not required for this deployment.
2. Review the development website after both the build and deploy jobs succeed.
3. When ready for stable publication, open and merge a **`dev` → `main`** PR.
   Actions renders and deploys the [stable website](https://gpid-wb.github.io/compound-gpid/).
   This promotes all changes included in that PR, including plugin changes.

After the pipeline is present on both branches, each push automatically
refreshes the corresponding channel. The Sites preview remains a separate
design-review snapshot.

## One source for every kind of content

| What changed? | Edit this source | What happens in the build |
|---|---|---|
| A guide, tutorial, or example | The appropriate `docs/**/*.md` page | A readable HTML page and searchable sections are rendered |
| Navigation or page description | `docs/navigation.json` | The sidebar, directory, breadcrumbs, and search metadata are updated |
| A new public page | Its Markdown file and navigation entry | Navigation coverage and generated links are checked |
| Command descriptions | Canonical `.github/prompts/` frontmatter | Managed command tables are regenerated |
| A release summary | Reviewed payloads in `releases/` | What's New is regenerated |
| Layout or interaction | `docs/index.html` and `docs/assets/` | The shared shell is applied to all rendered pages |
| Static rendering | `scripts/render-docs-site.js` and `scripts/docs-html.js` | HTML and search are regenerated from the same Markdown |

Keep authored prose outside `cg:auto` markers. Do not edit generated HTML or
`search-index.json`; they are build outputs. Platform projections are not a
second documentation source.

Automation keeps generated facts and publication synchronized. It cannot
invent a correct explanation of new behavior: the same feature PR must update
relevant procedures, examples, prerequisites, and limitations. CI catches
stale generated content, missing pages, and broken links; reviewers check the
meaning and usefulness of the guidance.

## Preview and check a change

With Node 22 or later, run from the repository root:

```bash
npm run docs:build
npm run docs:render
node scripts/check-rendered-docs.js .site
npm run docs:test
```

No `npm install` is required for these commands. `docs:build` regenerates
managed Markdown and validates the canonical documentation. `docs:render`
writes a disposable `.site/` directory with the homepage, one HTML page per
navigation entry, Markdown sources, assets, and a section-aware search index.
Serve `.site/` with a local static server to inspect it. The HTML itself is
readable without JavaScript; search and mobile controls enhance it.

Review generated Markdown changes before committing. For a no-write source
freshness check, use `npm run docs:check`. Never commit `.site/`.

## Automatic publication through GitHub Actions

1. **Pull request:** `Build combined documentation` runs on PRs targeting
   `main` or `dev`. It rebuilds, validates, tests, renders, checks HTML links
   and search destinations, and uploads a review artifact. It does not publish.
2. **Push:** `Deploy documentation site` checks out the exact triggering commit
   and the corresponding `main` and `dev` source revisions. Its read-only
   build job rebuilds both documentation trees from the plugin sources.
3. **Render:** the assembler renders supported shells into HTML, generates
   search, labels the development channel, and records both source SHAs and
   file digests. Older stable shells retain their own layout during migration.
4. **Verify:** the build checks source fingerprints, output digests, navigation,
   internal destinations, section anchors, and search coverage.
5. **Deploy:** a separate job rechecks the current branch heads and publishes
   the rendered artifact to GitHub Pages. Only this job receives Pages write
   and OIDC permissions; it checks out and executes no repository code.

Publication is serialized with the existing release publisher. A superseded
build refuses to replace a newer source state. The next push or a manual run
builds the current pair of branches. There is no manual copy to Sites and no
extra generated-docs PR needed for the website to refresh.

## Check an update or recover

1. Open the commit's [Actions runs](https://github.com/GPID-WB/compound-gpid/actions).
2. Confirm both the **build** and **deploy** jobs in **Deploy documentation
   site** succeeded. A successful build alone does not prove publication.
3. Open the appropriate handbook channel and verify the page and source commit.
4. Fix validation failures in source and push again. For a temporary service
   failure, rerun the workflow. Use **Run workflow** on `dev` or `main` for a
   clean rebuild; do not upload hand-edited artifacts.
5. If a branch moved, let its newer run publish, or dispatch a fresh run.
   If the `github-pages` environment requires approval, approve that deployment
   through GitHub's normal controls.

The existing release-tag workflow remains separate. Main's documentation bot
may propose generated Markdown changes for review; that PR is not the trigger
required for a development website update.

## Related guides

- [Contribute and Develop](../development/index.md)
- [Standard module](../workflows/standard.md)
- [Research handbook](../research/index.md)
