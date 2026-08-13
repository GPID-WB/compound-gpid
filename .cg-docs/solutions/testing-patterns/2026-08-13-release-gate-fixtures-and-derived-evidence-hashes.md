---
date: 2026-08-13
title: "Release-gate fixtures must mirror runtime commands and derived evidence hashes"
category: "testing-patterns"
language: "both"
tags: [release-gates, test-fixtures, generated-artifacts, sha256, provenance]
root-cause: "The release fixture omitted git tag discovery and asserted an obsolete source-checkout path, while a derived evidence manifest retained hashes from older generated views."
severity: "P1"
reviewed-in: ".cg-docs/reviews/2026-08-12-cr-local-evidence-workbench-revised-review.md"
related:
  - ".cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md"
  - ".cg-docs/solutions/bugs/2026-08-03-generic-publisher-secure-deletion-and-cross-platform-gates.md"
  - ".cg-docs/solutions/testing-patterns/2026-08-10-evidence-manifest-tests-require-referenced-files.md"
  - ".cg-docs/solutions/git-workflows/2026-08-11-merge-generated-brain-files-and-additive-ci-conflicts.md"
---

# Release-Gate Fixtures Must Mirror Runtime Commands and Derived Evidence Hashes

## Problem

The final release gate reported two failures in `test_release_gate_targets.py`:

- The checkout-mismatch test expected a tag mismatch, but the fake `git` executable did not implement `git -C <root> tag --list <tag>`. The release script therefore saw no matching tag and correctly skipped the mismatch comparison.
- The failing-preflight test expected Python to receive paths from the source checkout, while the release script intentionally clones `HEAD` into an isolated temporary checkout before running the preflight.

After those fixture failures were corrected, the artifact evidence validator found stale SHA-256 values for the brainstorm and plan HTML views in the committed design-evidence manifest.

## Root Cause

The release shim modeled only part of the runtime command protocol. It handled `rev-parse` and `status`, but not tag discovery, so it did not exercise the branch that the test claimed to cover. A second assertion encoded the old execution topology instead of the current contract: preflight paths are expected to point into a temporary clean clone.

The design-evidence JSON was derived state. The referenced HTML views had changed, but their recorded hashes were not regenerated, leaving a valid-looking manifest with incorrect provenance identities.

## Solution

Make the fixture mirror the commands used by the release script:

```sh
case "$1 $3" in
  '-C tag') printf '%s\n' "$CG_TAG_NAME" ;;
  '-C rev-parse') ... ;;
esac
```

Set `CG_TAG_NAME` in the fixture environment, then assert the current isolated-preflight contract without hard-coding a temporary directory:

```python
pytest_args = python_log.read_text(encoding="utf-8")
assert "compound-gpid-release-" in pytest_args
assert "scripts/tests/test_target_mapping.py" in pytest_args
```

Refresh derived evidence only from the referenced files and validate the complete manifest:

```sh
shasum -a 256 .cg-docs/views/brainstorms/<view>.html
shasum -a 256 .cg-docs/views/plans/<view>.html
python3 scripts/validate_artifact_view_evidence.py \
  --evidence .cg-docs/work-reports/2026-07-31-dual-audience-workflow-artifact-views.design-evidence.json \
  --require-all-pass
```

The release fixture then passed all 11 tests, the complete repository Python suite passed 778 tests with one skip, and artifact validation passed for both artifacts and all six viewports.

## Prevention

- When a shell fixture replaces an external CLI, mirror every command and argument shape that controls the production branch, including discovery commands such as `tag --list`.
- Assert stable semantic properties of isolated test runs, such as a temporary clone prefix and relative test names; do not assert obsolete absolute source paths.
- Treat generated HTML, screenshots, PDFs, and manifests as one provenance unit. Regenerate hashes whenever a referenced artifact changes.
- Run the release gate against clean committed `HEAD`; a dirty-worktree success is not release evidence.
- Require existence, non-empty content, and exact hash equality for every manifest reference; never make hash checks conditional on file existence.

## Related

- [Cross-agent native platform trees require a generator, drift tests, and consistent Python resolution](../environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md)
- [Generic publisher deletion commit points and cross-platform release gates](../bugs/2026-08-03-generic-publisher-secure-deletion-and-cross-platform-gates.md)
- [Evidence manifest tests must require referenced files to exist and be non-empty before hashing](2026-08-10-evidence-manifest-tests-require-referenced-files.md)
- [Merge strategy for generated Brain files and additive CI matrix conflicts](../git-workflows/2026-08-11-merge-generated-brain-files-and-additive-ci-conflicts.md)
