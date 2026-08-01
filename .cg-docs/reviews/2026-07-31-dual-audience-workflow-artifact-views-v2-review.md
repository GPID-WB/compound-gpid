---
date: 2026-07-31
depth: full
mode: auto
plan: ".cg-docs/plans/2026-07-31-dual-audience-workflow-artifact-views-v2.md"
findings:
  P0.1: open
  P0.2: open
  P0.3: open
  P0.4: open
  P1.1: open
  P1.2: open
  P1.3: open
  P1.4: open
  P1.5: open
  P1.6: open
  P1.7: open
  P1.8: open
  P1.9: open
  P1.10: open
  P1.11: open
  P2.1: open
  P2.2: open
  P2.3: open
  P2.4: open
---

# Review: Dual-Audience Workflow Artifact Views (V2)

## Summary

**Review mode**: full, auto-routed for schema, secure-filesystem, installer,
and generated-target risk.

**Result**: implementation and evidence gates ran successfully, but the
independent review found merge-blocking security and correctness gaps. Duplicate
agent findings are consolidated below. No fixes were applied during this review
handoff.

## P0 - Blocking

### P0.1 - Fallback secure replacement has a residual TOCTOU gap

- **Files**: `scripts/secure_fs.py:256-293`,
  `scripts/artifact_views/tests/test_writer.py:81-103`
- **Finding**: The fallback snapshots ancestors, writes a temporary file, checks
  identities, and then uses pathname-based `os.replace()`. An ancestor can be
  swapped after the final check. The fallback can also create/write the
  temporary file outside the intended root if the parent is replaced before
  `mkstemp()`.
- **Required fix**: Use handle-relative native mutation on Windows or fail closed
  where a pinned replacement cannot be guaranteed. Add a real fallback/Windows
  mutation-boundary race test.

### P0.2 - Canonical source read is not pinned or no-follow

- **Files**: `scripts/artifact_views/paths.py:84-103`,
  `scripts/artifact_views/cli.py:147-148`
- **Finding**: Path validation and `read_bytes()` are separate pathname
  operations. A source or ancestor can change to a link between them.
- **Required fix**: Read through a root-pinned no-follow descriptor, verify the
  opened file identity/type, and add a source-swap race test.

### P0.3 - `--check` can accept tampered HTML as current

- **Files**: `scripts/artifact_views/cli.py:76-113`,
  `.github/prompts/cg-commit-push-pr.prompt.md`
- **Finding**: Freshness trusts selected provenance fields but does not validate
  or reproduce the remaining HTML. An altered body or removed CSP can retain a
  valid provenance script and pass the path-only commit gate.
- **Required fix**: Parse the complete provenance, rerender with its timestamp,
  run final HTML security validation, and require exact byte equality.

### P0.4 - New secure-writer files bypass the process umask

- **File**: `scripts/secure_fs.py:397-403`
- **Finding**: New files default to `0666`, or `0777` when executable, and are
  explicitly applied with `fchmod`/`chmod`.
- **Required fix**: Default new regular files to `0644` and executables to
  `0755`, while preserving existing modes. Add restrictive-umask tests.

## P1 - Critical

### P1.1 - Native Windows relative paths are rejected

- **Files**: `scripts/secure_fs.py:36-60`, `scripts/artifact_views/writer.py`,
  `scripts/cg_generate_targets.py`
- **Finding**: Native `WindowsPath` strings contain backslashes, but the shared
  writer rejects backslashes before normalization.
- **Fix**: Normalize native path components to a canonical relative POSIX form
  before validation; add Windows path contract tests.

### P1.2 - CMD wrapper can lose Python's failure status

- **Files**: `bin/cg-render-artifact.cmd`, `tests/install.Tests.ps1`
- **Finding**: `%ERRORLEVEL%` inside parenthesized blocks may be expanded before
  Python runs, allowing failed validation to return success.
- **Fix**: Select the interpreter in probe blocks, execute outside them, and
  propagate the fresh exit status. Audit sibling Python CMD launchers and add an
  executed Windows nonzero-status test.

### P1.3 - Table parsing can silently lose canonical cells

- **Files**: `scripts/artifact_views/parser.py:191-229`,
  `scripts/artifact_views/renderer.py:212-221`
- **Finding**: Duplicate normalized headers overwrite dictionary keys, surplus
  cells disappear, and missing cells are synthesized. Block-level coverage does
  not detect cell loss.
- **Fix**: Reject empty/duplicate headers and row-width mismatches, preserving
  ordered cell identity in tests.

### P1.4 - Scope and Required values fail open

- **Files**: `scripts/artifact_views/validator.py:435-437`,
  `scripts/artifact_views/parser.py:804-821`
- **Finding**: An invalid scope skips Standard/Deep coverage. Any Required token
  other than exact `yes` becomes optional, and blank-ID rows can disappear.
- **Fix**: Strictly validate frontmatter types/enums, `Required: yes|no`, row IDs,
  and required evidence usability before deriving behavior.

### P1.5 - Completion-contract rules disagree across scopes

- **Files**: `.github/prompts/cg-plan.prompt.md`,
  `.github/shared/goal-execution.contract.md`,
  `scripts/artifact_views/schema.py`, `scripts/artifact_views/validator.py`
- **Finding**: Canonical instructions allow a condensed Lightweight contract,
  while strict version 1 validation requires all six subsections. Constraint
  rows also lack complete phase/cell validation.
- **Fix**: Define one strict version 1 contract across docs, schema, validator,
  fixtures, and Pester tests; reserve condensed handling for explicit legacy
  input if retained.

### P1.6 - Design evidence is not cryptographically or semantically bound

- **Files**: `scripts/artifact_views/evidence.py`,
  `scripts/artifact_views/tests/test_evidence.py`, design evidence JSON
- **Finding**: Screenshots/PDFs need only be nonempty and required booleans are
  caller assertions. Viewport dimensions, file signatures, evidence hashes,
  canonical path mapping, and view provenance are not verified.
- **Fix**: Hash every evidence file; validate PNG dimensions/signatures, PDF
  structure, source/view mapping and provenance, strict timestamps/JSON, and
  structured machine measurements for required booleans.

### P1.7 - Symlink aliases can bypass view-body exclusions

- **Files**: `scripts/brain/scanner.py`, `scripts/cg_audit_context.py`
- **Finding**: A lexical Plan path symlinked to a file under `views/` is
  classified by the alias and can enter model context.
- **Fix**: Reject symlink inputs and apply exclusions to lexical and resolved
  paths. Add Brain and audit alias-sentinel tests.

### P1.8 - Uninstall deletes committed wrapper sources

- **Files**: `install.ps1`, `scripts/install.sh`
- **Finding**: Uninstall removes every `cg-*` file from the repository-owned
  `bin/`. Reinstall cannot restore committed source-of-truth wrappers after they
  are deleted.
- **Fix**: Unregister PATH/profile state while preserving repository-owned
  wrapper files, or separate installed copies from committed sources.

### P1.9 - Fenced examples can satisfy step metadata

- **File**: `scripts/artifact_views/parser.py:743-765`
- **Finding**: Label extraction regex-searches every block, including fenced code
  and raw HTML, so example text can satisfy Requirements or Tests metadata.
- **Fix**: Parse labels only from the documented list-item structure and retain
  the actual source block ID.

### P1.10 - Charterless projects contradict CLI root discovery

- **Files**: `scripts/artifact_views/cli.py:43-67`,
  `docs/configuration/index.md`
- **Finding**: Documentation says the charter is optional, but ordinary root
  discovery requires `compound-gpid.md`.
- **Fix**: Support other reliable project boundaries and test root, nested, and
  absolute-source invocation without hidden `--root`.

### P1.11 - Claimed Python 3.8 compatibility is incomplete

- **Files**: `scripts/cg_summary.py`, installers/launchers/CI
- **Finding**: Runtime `Path.is_relative_to()` requires Python 3.9, while
  launchers accept any Python version and current CI does not execute the new
  artifact suite on Python 3.8/Windows.
- **Fix**: Replace 3.9-only APIs, enforce `>=3.8`, and add artifact/evidence and
  Windows launcher gates to CI/release preflight.

## P2 - Important

### P2.1 - Public API and complete-reference documentation gaps

Several public functions lack full Args/Returns/Raises/examples, the complete
reference omits `cg-render-artifact`, and installation inventories omit the new
command and Python dependency behavior.

### P2.2 - Evidence binaries add substantial repository weight

The ten PNG/PDF evidence files total about 27 MiB. Decide whether to optimize
those exact files or manage them with targeted Git LFS rules before commit.

### P2.3 - CI and release gates do not enumerate the new suites

The repository workflow and release preflight should explicitly execute the
artifact-view, scanner, summary, evidence, and generated-target checks required
by V1-V11.

### P2.4 - Long malformed inline content can become quadratic

`render_safe_inline()` repeatedly scans the remaining string for unmatched
brackets or angle brackets. Replace it with bounded single-pass tokenization and
add an adversarial scaling test.

## Passed Areas

- Exact V1-V11 commands were executed with documented clean-HEAD mirror handling.
- Generated target ownership, closure, determinism, and parity passed.
- Canonical workflow hooks and model-context path-only contracts passed.
- Renderer CSP/raw-HTML escaping and exact source-block ownership tests passed.
- No generated `.cg-docs/views/**` bodies were loaded by review agents.

## Recommended Handoff

Run `/cg-fix-triage P0 P1` before merge. Re-run a full review after fixes, with
actual Windows execution evidence for the secure fallback and CMD launcher.
