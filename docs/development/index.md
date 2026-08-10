# Contribute and Develop

Repository contributors must preserve cross-platform behavior, canonical-to-
generated target parity, documentation accuracy, and safe test execution.

## Development path

1. Create a conventional feature or fix branch from `main`.
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

- `docs/navigation.json` is the public route, navigation, and search manifest.
- Every published Markdown page must be represented in the manifest.
- `.github/skills/` is canonical for the skills catalog; generated mirrors do
  not add catalog entries.
- Preserve useful content by migrating, condensing, linking, or explicitly
  labeling it obsolete.
- Update internal links and fragments when moving headings.
- Preview the static site over HTTP because browser `fetch()` does not work
  correctly from a local `file://` URL.

GitHub Pages validates the site and uploads `docs/` directly. The Markdown link
workflow also checks repository documentation.

## Maintainer references

- [Competitive Reviews](../competitive-reviews.md)
- [Documentation Migration](../about/documentation-audit.md)
- [Complete Reference](../reference.md)
- [Modular Guide](../modular-guide.md)
