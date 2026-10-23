# Contribute and Develop

Repository contributors must preserve cross-platform behavior, canonical-to-
generated target parity, documentation accuracy, and safe test execution.

## Development path

1. Create a conventional feature or fix branch from the current `dev` branch.
2. Change canonical sources, not generated mirrors.
3. Add or update focused tests with the behavior change.
4. Regenerate native target trees when canonical `.github/` assets change.
5. Update the relevant page and navigation when public behavior changes.
6. Run narrow checks, then the canonical full test runner when required.
7. Review the diff for credentials, data, accidental generated churn, and
   substantive documentation loss.

See the repository
[CONTRIBUTING.md](https://github.com/GPID-WB/compound-gpid/blob/main/CONTRIBUTING.md)
for platform setup, CI, parity, conventional commits, PR workflow, and the full
self-review checklist.

## Run tests safely

Before target tests, validate the modular registry:

```bash
python scripts/cg_validate_modules.py --check-ownership --check-dependencies --check-cross-suite
python scripts/cg_generate_targets.py --all --dry-run
python -m pytest scripts/tests -q
```

These gates cover one-owner inventory, acyclic layer dependencies, cross-suite
isolation, CG/CR characterization, context budgets, and all five runtime targets.

This repository requires Pester 4.10.1. Never run `Invoke-Pester tests/`
directly and never pipe `-PassThru` output into `Select-Object
-ExpandProperty TestResult`.

Use the canonical runner:

```powershell
. tests\Run-Tests.ps1
```

Run a registered narrow file by stem when appropriate:

```powershell
. tests\Run-Tests.ps1 -File link
```

Documentation-site validation is independent and can run with Node:

```bash
node scripts/check-docs-site.js
```

## Documentation maintenance

The [documentation publishing guide](../about/publishing.md) explains source
ownership, page organization, local checks, automatic development publication,
and recovery. Start there when editing the website.

```bash
npm run docs:build
npm run docs:test
```

Every push to `dev` rebuilds the exact commit and hands its verified artifact to
the protected publisher on `main`. The development handbook updates at
[the /dev/ address](https://gpid-wb.github.io/compound-gpid/dev/); the stable
[site root](https://gpid-wb.github.io/compound-gpid/) remains the reviewed release
snapshot. Use the channel switch in the sidebar to move between them.

`docs/navigation.json` owns page routes, grouping, descriptions, and discovery.
Every public Markdown page appears once. The website reads the canonical
Markdown directly; `cg:auto` marker interiors are regenerated and manual text
outside them is preserved. No manual upload is needed.

### What's New page

`docs/whats-new.md` is an auto-managed page whose `release-notes` section is
generated from `releases/*.json` release payloads. Release payloads are the
durable public-release source for the page; the GitHub Release remains the public
release record. `RELEASE_NOTES.md` stays ephemeral and gitignored.

### Release tag policy

Compound GPID supports two release tag forms:

| Tag form | Purpose | GitHub release type |
|----------|---------|---------------------|
| `v<major>.<minor>.<patch>` | Stable release | Release |
| `v<major>.<minor>.<patch>.<build>` | Installable test release, conventionally using build numbers `9000+` | Prerelease |

Pass an exact tag to `/cg-release` when preparing a test release:

```text
/cg-release v1.2.0.9008
```

The four-component form is a first-class release identifier, not malformed
semver input. `/cg-release` accepts it for new and resumed releases and always
passes `-Prerelease` to `create-release.ps1`. Three-component tags remain the
stable channel. Published release tags and immutable payloads must not be
deleted or reused.

After GitHub release publication, `create-release.ps1` runs
`scripts/cg_release_attestation.py`. It records the annotated tag object, peeled
commit, immutable payload SHA-256, and every tagged deprecation-record digest in
`.github/shared/skill-management/release-attestations/<tag>.json`. This reviewed
post-release artifact provides future plugin-removal grace evidence and must not
be edited or backfilled by hand.

Stable releases must be prepared from a clean `main` checkout matching
`origin/main`. Four-component prereleases must be prepared directly from a
clean `dev` checkout matching `origin/dev`; their exact tag remains eligible for
resume after `dev` advances.

Repository settings must include an active tag ruleset named `Protect release
tags` for `refs/tags/v*`. It must block updates, non-fast-forward updates, and
deletions without exclusions or bypass actors so a verified release tag cannot
move during publication. A separate `Restrict release tag creation` ruleset
allows only repository administrators to create `refs/tags/v*`; `Protect dev`
blocks deletion and force-pushes on `refs/heads/dev` without bypass actors.
Tag commits build documentation in the read-only `release-docs.yml` workflow;
the protected-main `release-pages.yml` controller verifies and deploys that
prebuilt artifact without executing tagged repository code with Pages access.

### Release payload schema

Immutable, tracked files named `releases/v<major>.<minor>.<patch>[.<dev>].json`;
`releases/latest.json` is a byte-for-byte current-release convenience copy and is
never rendered as a second release.

| Field | Required | Value |
|-------|----------|-------|
| `schemaVersion` | yes | `1` |
| `tag` | yes | stable or prerelease tag (e.g. `v1.2.3` or `v1.2.3.9000`) |
| `publishedAt` | yes | UTC ISO-8601 |
| `name` | yes | release title |
| `url` | yes | GitHub release URL shape |
| `sourceUrl` | yes | exact pushed GitHub tag URL (`.../tree/<tag>`) |
| `sections` | yes | non-empty array |

Each section has a controlled `kind` (`new`, `fixed`, or `internal`), a bounded
plain-text title, and bounded plain-text entries. Malformed tags, duplicate
tags, malformed dates, unknown fields that alter rendering semantics, control
characters, invalid GitHub release or source-tag URLs, and excessive record sizes are
rejected before write. The page renders at most the 20 newest immutable
payloads (newest first by `publishedAt` then tag) and links to GitHub Releases
for older history.

Local payload validation (the machine-checkable guard before any payload
commit):

```bash
node scripts/generate-whats-new.js --validate-payload releases/v1.2.3.9000.json
```

### Deployment behavior

The Pages workflow deploys only the unmodified, complete, validated,
digest-verified post-build artifact. Stale main-branch runs are skipped by the
normalized canonical-input fingerprint check; immutable release tags and manual
dispatches build complete trees directly. No workflow depends on a bot push
triggering a second workflow.

### Recovery behavior

- No-op rebuild: `docs/` unchanged — no bot commit; the artifact is still
  uploaded for Pages.
- Validation failure: the rebuild fails loudly and never deploys.
- Stale run: a rebuild that finished after a newer canonical `main` commit is
  skipped by Pages rather than deployed.
- Bot commit: only `docs/` is staged with a conventional message stating it is
  a deterministic render from the approved canonical inputs.
- Release API failure: the committed/tagged payload source state remains
  recoverable; a maintainer can resume without overwriting a release record.
