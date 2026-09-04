---
date: 2026-09-02
title: "Secure c-research migration and research-output boundary"
category: "bugs"
language: "both"
tags: [c-research, migration, filesystem, security, symlink, toctou, evidence, provenance, suites, generated-targets]
root-cause: "The first layout migration relied on pathname checks followed by ordinary copy/delete operations, while the output-only and canonical-authority boundaries were not enforced by executable contracts."
severity: "P0"
---

# Secure c-research Migration and Research-Output Boundary

## Problem

Moving Compound Research outputs from `.cg-docs/research/` to the root-level
`c-research/` workspace exposed several correctness and safety failures:

- A symlinked `.cg-docs/` ancestor could expose an external source tree to the
  migrator.
- A dangling destination symlink could make `Path.exists()` return false and
  redirect an ordinary copy outside the repository.
- `copy2()` followed by `unlink()` was vulnerable to destination races, source
  replacement, partial publication, and source loss after a concurrent change.
- Apply mode could remove legacy files while live operational references still
  pointed at the old path.
- Any regular file under an accepted legacy artifact directory could be moved,
  including data, source documents, code, or other inputs.
- The evidence runtime checked only the leaf evidence directory, allowing
  symlinked ancestors or derived descendants to redirect writes.
- Two materially different practitioner-tour manuscripts existed, and the
  presentation deck's 21 sections matched the legacy draft rather than the
  initially migrated 16-slide draft.

## Root Cause

A pathname is not a stable filesystem identity. Checking a path with `exists()`,
`is_symlink()`, `stat()`, or a content hash does not authorize a later pathname
mutation because another process can replace an ancestor or final directory
entry between the check and the operation.

The migration also treated directory membership as proof of output ownership.
That conflicted with the approved boundary: `c-research/` is output-only, while
`data/`, source documents, and code are inputs held elsewhere. Finally, the
migration treated byte conflicts as a path problem without resolving which
research artifact was authoritative for the derived presentation.

## Solution

### Root-anchored, no-follow migration

The migration now uses the shared `secure_fs` primitives from the project root:

```python
content = secure_read_bytes(
    project_root,
    source_relative,
    reject_hardlinks=True,
)
secure_write_bytes(
    project_root,
    destination_relative,
    content,
    expected_state=ExpectedFileState.absent(),
)
secure_delete_verified(project_root, source_relative, digest)
```

The implementation rejects symlinked ancestors, detects dangling destination
links, publishes through temporary same-directory files with non-clobbering
semantics, rechecks source and destination bytes, and restores the source if a
post-delete destination check fails. Apply mode blocks before mutation when
operational legacy references remain.

Every legacy file now requires explicit `--allow-output <project-relative-path>`
approval. Reserved input directories such as `data`, `raw`, `source`, and `code`
are always rejected. The migrator creates the complete fixed `c-research/`
scaffold only after verified migration.

### Evidence containment

`validate_path_components()` rejects unsafe existing ancestors while permitting
standard macOS `/private` aliases. The evidence store opens its lock through a
no-follow directory handle, and the lexical index revalidates its storage path
before public operations. Resource observation reads through a pinned,
no-follow handle and rejects hard-link aliases and identity replacement.

### Canonical authority and suite behavior

The 21-slide practitioner manuscript that matches the 21-section Reveal.js deck
is canonical. The 16-slide version is retained under an explicit superseded
alternate filename. The legacy research root is removed only after that choice
and the migration check succeeds.

The native target trees remain a shared all-suite distribution baseline because
linked projects share the global installation. `suites:` controls project-level
workflow eligibility and instruction loading; `--active-suites` remains an
explicit option for isolated maintainer builds and does not rewrite the shared
tree for one consumer. Model metadata remains advisory-only and platform-picker
selection remains authoritative.

## Prevention

- Treat path validation and filesystem mutation as one security boundary. Use
  root-anchored, no-follow handles and non-clobbering publication for writes,
  deletes, and rollback.
- Revalidate source identity immediately before publication and verify the
  destination before removing the source.
- Fail closed on operational stale references, ambiguous input files, unknown
  artifact directories, symlinks, dangling links, and byte conflicts.
- Require an explicit manifest or per-file classification when a migration cannot
  prove that a file is a research output.
- Keep canonical research outputs under `c-research/`, process records under
  `.cg-docs/`, and project inputs under separate `data/` or source locations.
- Resolve derived-artifact authority by comparing structure and provenance, not
  by choosing the first path that happens to exist.
- Treat linked native targets as a shared distribution baseline; never apply one
  consumer's suite filter to the global installation.
- Add behavioral race, symlink, conflict, stale-reference, authority, and
  updater tests. Source-text assertions alone do not prove script behavior.

The completed fix passed 890 repository Python tests with one
platform-appropriate skip, 122 evidence-package tests with one dependency
warning, 2,446 safe Pester tests with three environment-appropriate skips, the
migration `--check` (`up-to-date`), plan validation, Brain rebuild, diagnostics,
and `git diff --check`.

## Related

- [Filesystem race fixes require handle-relative mutation and real boundary tests](../testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md)
- [Secure publication and rollback must not clobber concurrent filesystem changes](2026-08-01-secure-publication-rollback-must-not-clobber.md)
- [Python path containment must use component-aware checks](2026-05-20-python-path-startswith-bypass-use-relative-to.md)
- [Root-level c-research migration review](../../reviews/2026-09-02-c-research-output-workspace-migration-review.md)
- [c-research output workspace](../../../c-research/README.md)
