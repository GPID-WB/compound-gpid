# Keep the Documentation Current

Edit the documentation in the repository. GitHub Pages is the maintained public
website; a Sites preview is a review snapshot of the same files.

## Which website should I use?

| Channel | Address | When it changes |
|---|---|---|
| Latest development docs | [Development handbook](https://gpid-wb.github.io/compound-gpid/dev/) | Automatically after a successful build of each push to `dev` and verification by the protected publisher |
| Stable docs | [Stable handbook](https://gpid-wb.github.io/compound-gpid/) | When the protected release publisher accepts a reviewed release snapshot |

Use the development handbook when following `dev`. The stable handbook describes
the published release and can deliberately differ from development. The channel
label and switch in the sidebar make that distinction visible. Development
publication preserves the official stable snapshot.

## Where should I make a change?

| What changed? | Edit this source | Then check |
|---|---|---|
| A procedure or explanation | The appropriate `docs/**/*.md` page | Links, examples, and the reader's next step |
| A page's position or label | `docs/navigation.json` | Each public Markdown page appears exactly once |
| A new public page | Its Markdown file and `docs/navigation.json` | A useful title, description, and task-oriented group |
| Command descriptions | Canonical `.github/prompts/` frontmatter | Rebuild the managed command tables |
| A release summary | The reviewed release payload in `releases/` | Rebuild What's New through the release process |
| Layout or interaction | `docs/index.html` and `docs/assets/` | Desktop, mobile, keyboard navigation, and search |

`cg:auto` marker interiors are generated. Keep hand-written guidance outside
those markers; the rebuild preserves it. Generated target trees are not a
second documentation source.

## Before opening a pull request

Work from the current `dev` branch for development documentation. Read the page
as someone completing a task: explain the first action, link to prerequisites,
and place exhaustive contracts in reference pages.

Run these commands from the repository root with Node 22 or later. They use
Node's standard library and do not require `npm install`:

```bash
npm run docs:build
npm run docs:test
```

The build regenerates the command tables and What's New page, checks public
navigation coverage and internal Markdown links, and produces file digests.
Review any generated Markdown changes before committing. For a no-write check:

```bash
npm run docs:check
```

The website reads the same Markdown files used on GitHub. Search builds a local
in-memory index of those pages when first used; no external search service or
separate editable index is involved. Results prioritize titles and headings,
and link to the matching section. A partial loading failure is shown explicitly.

## Automatic development publication

1. A pull request to `dev` or `main` runs **Build combined documentation** as a
   read-only validation job. It rebuilds, validates, runs documentation tests,
   checks compatibility with the current protected publisher, and uploads the
   proposed docs for review. Pull requests do not publish.
2. Every push to `dev` runs **Deploy documentation site**. There is no path
   filter, so a newly introduced documentation input cannot be missed. The
   workflow checks out the exact triggering commit, rebuilds and validates its
   complete docs, and uploads `legacy-dev-docs` with build metadata.
3. The existing **Deploy release documentation** workflow on protected `main`
   receives that successful run. It checks actor authority, producer identity,
   artifact digests, canonical source derivation, and current `dev` freshness
   before publishing the preview alongside the preserved stable snapshot.

The producer receives read-only repository access. Only the protected
publisher receives Pages write access. Keep the producer workflow name and
`legacy-dev-docs` artifact name intact: the publisher uses them to identify the
handoff. Do not edit the canonical documentation generator casually; the
protected publisher recognizes its code identity.

No manual copy to another website and no generated-docs pull request are needed
to update `/dev/`. Publishing can still be blocked by a failed check, changed
permissions, or a newer commit superseding the build.

## Check an update and recover a failed publication

1. On the commit's [Actions page](https://github.com/GPID-WB/compound-gpid/actions),
   confirm **Deploy documentation site** succeeded.
2. Confirm its matching **Deploy release documentation** run succeeded. A
   successful build alone is not evidence of deployment.
3. Open the development handbook, reload, and verify the changed page. Check the
   channel label if the stable page still shows the released behavior.
4. For a build or validation failure, fix the source and push again. For a
   temporary publisher failure, inspect its logs and rerun the protected
   publisher after resolving the cause. To create a new producer run, use
   **Run workflow** on `dev`; do not upload hand-edited artifacts.

The older **Rebuild documentation** and release workflows remain separate
stable/release maintenance paths. A bot's draft documentation PR is a proposal
for tracked Markdown updates, not proof that the public site was refreshed.

## Related guides

- [Contribute and Develop](../development/index.md)
- [Getting Started](../getting-started/index.md)
- [What's New](../whats-new.md)
