---
date: 2026-07-31
depth: light
parent-review: .cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md
type: verification
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: skipped
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P1.12: fixed
  P1.13: skipped
  P2.1: fixed
  P2.2: skipped
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
---

# Verification Review: Artifact Views

## Review Report

**Review mode**: light (`mode:verify`)
**Parent review**: `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md`
**Files reviewed**: current changed-file scope, excluding generated `.cg-docs/views/**` bodies and diffs
**Findings**: 23 (P0: 4, P1: 13, P2: 6, P3: 0)

The selected parent review is the newest eligible standard review with explicitly
fixed findings. Its fixed scope concerns WB report-writing contracts and does not
cover the artifact-view implementation. Therefore no current P2/P3 finding was
suppressed. P0/P1 and cross-file breakage are always reportable.

## P0 - BLOCKING

### P0.1 - Fallback secure replacement retains a TOCTOU escape

- **Files**: `scripts/secure_fs.py:256-293`, `scripts/artifact_views/tests/test_writer.py:81`
- **Why**: The fallback snapshots ancestor identities and later performs
  pathname-based `os.replace()`. An ancestor can change after the final check;
  the existing mutation-boundary test is POSIX-only.
- **Fix**: Use pinned handle-relative Windows mutation or fail closed when it is
  unavailable. Add an actual fallback/Windows mutation-boundary race test.

### P0.2 - Canonical source validation and reading are raceable

- **Files**: `scripts/artifact_views/paths.py:86`, `scripts/artifact_views/cli.py:147`
- **Why**: Source path validation and `read_bytes()` are separate pathname
  operations, allowing a source or ancestor swap between them.
- **Fix**: Read through a root-pinned no-follow descriptor and verify the opened
  file identity and type.

### P0.3 - `--check` accepts tampered HTML as current

- **Files**: `scripts/artifact_views/cli.py:98-113`, `.github/prompts/cg-commit-push-pr.prompt.md`
- **Why**: Freshness trusts selected provenance fields but not the rest of the
  HTML. A changed body or removed CSP can retain the provenance block and pass
  the path-only commit gate.
- **Fix**: Validate complete provenance, rerender using its timestamp, run final
  HTML security validation, and require exact byte equality.

### P0.4 - New secure-writer files bypass restrictive umasks

- **File**: `scripts/secure_fs.py:398`
- **Why**: New files are explicitly changed to `0666`, or `0777` when
  executable, regardless of process umask.
- **Fix**: Default new files to `0644` and executables to `0755`, while
  preserving existing modes. Add restrictive-umask tests.

## P1 - CRITICAL

### P1.1 - Native Windows relative paths are rejected

- **Files**: `scripts/secure_fs.py:55`, `scripts/cg_generate_targets.py:1084`
- **Why**: Native Windows paths contain backslashes, which are rejected before
  normalization, breaking nested view and generated-target writes.
- **Fix**: Normalize native components to a canonical POSIX-relative form before
  validation and add Windows path tests.

### P1.2 - CMD launchers can lose the child failure status

- **Files**: `bin/cg-render-artifact.cmd:8-12`, `bin/cg-index.cmd`,
  `bin/cg-brain-init.cmd`, `bin/cg-token-audit.cmd`, `tests/install.Tests.ps1`
- **Why**: `%ERRORLEVEL%` inside parenthesized probe blocks can be expanded before
  Python finishes. Static tests currently accept the broken literal.
- **Fix**: Select the interpreter inside probes, execute outside the block, and
  add Windows behavioral tests for exact nonzero propagation. Audit all sibling
  Python launchers in the same change.

### P1.3 - Table parsing can silently lose canonical cells

- **Files**: `scripts/artifact_views/parser.py:217`, `scripts/artifact_views/renderer.py:212`
- **Why**: Duplicate normalized headers overwrite cells, surplus cells vanish,
  and missing cells are synthesized. Block-level coverage cannot detect this.
- **Fix**: Reject empty or duplicate headers and every row-width mismatch.

### P1.4 - Invalid scope values bypass coverage validation

- **Files**: `scripts/artifact_views/validator.py:435`, `.github/prompts/cg-plan.prompt.md`
- **Why**: Scope is not enum-validated; values such as `deep` skip exact
  Standard/Deep requirement-coverage checks.
- **Fix**: Validate canonical Plan and Brainstorm scope enums before any
  scope-dependent behavior, with invalid-scope negative tests.

### P1.5 - Invalid Required values become optional

- **Files**: `scripts/artifact_views/parser.py:818`, `scripts/artifact_views/validator.py:545`
- **Why**: Any value other than case-insensitive `yes`, including blanks and
  typos, becomes false and bypasses evidence checks.
- **Fix**: Validate raw Required cells as exactly `yes|no` before conversion.

### P1.6 - Lightweight completion-contract rules contradict strict validation

- **Files**: `.github/prompts/cg-plan.prompt.md:170`,
  `.github/shared/goal-execution.contract.md:38`,
  `scripts/artifact_views/schema.py:139`, `scripts/artifact_views/validator.py`
- **Why**: Canonical instructions permit a condensed Lightweight contract while
  strict schema version 1 requires all six subsections.
- **Fix**: Choose one version 1 contract and align prompts, shared contract,
  schema, validator, fixtures, generated targets, and behavioral tests.

### P1.7 - Design evidence remains self-attested

- **Files**: `scripts/artifact_views/evidence.py:130-167`,
  `scripts/artifact_views/tests/test_evidence.py`
- **Why**: Screenshot/PDF files need only be nonempty, booleans are caller
  assertions, and the Open Design image field is ignored.
- **Fix**: Validate hashes, signatures, dimensions, path/provenance mapping, and
  structured machine-produced measurements.

### P1.8 - Symlink aliases can bypass view-body exclusions

- **Files**: `scripts/brain/scanner.py:87`, `scripts/cg_audit_context.py:378`
- **Why**: Classification/exclusion uses lexical paths even when a permitted
  alias resolves into `.cg-docs/views/`.
- **Fix**: Reject symlink inputs and apply exclusions to lexical and resolved
  paths, with alias-sentinel tests.

### P1.9 - Uninstall deletes repository-owned wrapper sources

- **Files**: `install.ps1:51`, `scripts/install.sh:91`
- **Why**: Uninstall removes every `cg-*` file from the repository-owned `bin/`,
  including committed source-of-truth wrappers needed by reinstall.
- **Fix**: Remove PATH/profile registration while preserving repository-owned
  wrappers, or install separate owned copies.

### P1.10 - Fenced examples can satisfy step metadata

- **File**: `scripts/artifact_views/parser.py:749`
- **Why**: Metadata extraction regex-searches fenced code and raw HTML, so sample
  text can satisfy Requirements or Tests.
- **Fix**: Accept labels only from the documented list-item block structure and
  retain the actual source block ID.

### P1.11 - Charterless projects contradict CLI root discovery

- **Files**: `scripts/artifact_views/cli.py:48`, `docs/configuration/index.md:28`
- **Why**: Documentation permits projects without `compound-gpid.md`, but normal
  root discovery requires that file.
- **Fix**: Recognize another stable project boundary or document the charter as
  a renderer prerequisite; test root, nested, and absolute-source invocations.

### P1.12 - Claimed Python 3.8 compatibility is incomplete

- **Files**: `scripts/cg_summary.py:118`, `bin/cg-render-artifact`, installers
- **Why**: `Path.is_relative_to()` requires Python 3.9, and launchers accept any
  Python major/minor version.
- **Fix**: Replace 3.9-only APIs, enforce Python 3.8+, and add compatibility
  execution gates.

### P1.13 - Plan validation hook is ordered before the real save block

- **Files**: `.github/prompts/cg-plan.prompt.md:165-207`,
  `tests/prompt-tools.Tests.ps1:6247`
- **Why**: The validation instructions precede the actual approved Save block;
  the Pester assertion anchors an earlier generic “Write the plan” phrase.
- **Fix**: Move validation immediately after the real save operation and assert
  ordering against that exact block.

## P2 - IMPORTANT

### P2.1 - Complete reference and public API documentation are incomplete

- **Files**: `docs/reference.md`, `docs/installation.md`, public functions under
  `scripts/artifact_views/`
- **Fix**: Add the complete command/config/exit-code lifecycle and finish required
  Args, Returns, Raises, and examples.

### P2.2 - CI and release gates omit the new suites

- **Files**: `.github/workflows/tests.yml`, `create-release.ps1`
- **Fix**: Run artifact-view, evidence, scanner, summary, and Windows launcher
  suites in CI/release preflight.

### P2.3 - Malformed inline input can trigger quadratic scans

- **File**: `scripts/artifact_views/security.py:75`
- **Fix**: Replace repeated remaining-string searches with bounded single-pass
  tokenization and add a scaling test.

### P2.4 - Nested list hierarchy is flattened

- **File**: `scripts/artifact_views/renderer.py:192`
- **Fix**: Preserve list nesting or render unsupported nested structures visibly
  as raw source rather than silently flattening them.

### P2.5 - Byte-ledger tests do not prove exact source reconstruction

- **Files**: `scripts/artifact_views/model.py:359`, parser/model tests
- **Fix**: Assert concatenated raw blocks exactly reconstruct source bytes for
  BOM, Unicode, CRLF, and no-final-newline fixtures.

### P2.6 - Shared state vocabularies lack a cross-file invariant

- **Files**: `scripts/artifact_views/schema.py`, validator tests, canonical
  prompts/contracts, Pester tests
- **Fix**: Add parameterized invalid-state tests and one invariant comparing
  documented status/deviation/scope vocabularies with executable owners.

## Passed

- Both review agents produced usable, file-grounded output.
- Model-context exclusions and canonical/generated parity retain focused sentinel
  and drift coverage.
- Renderer/writer failure preservation remains covered.
- No generated `.cg-docs/views/**` body or diff was read.

## Verification Result

The cycle has **not converged**. No fixes were applied in verification mode.
Resolve P0/P1 findings before merge, then rerun `/cg-review mode:verify`.
