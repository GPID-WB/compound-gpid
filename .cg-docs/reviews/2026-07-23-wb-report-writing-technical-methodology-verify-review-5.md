---
date: 2026-07-31
depth: light
parent-review: .cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md
type: verification
findings:
  P0.1: fixed
  P0.2: fixed
  P1.1: skipped
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: skipped
  P1.6: fixed
  P1.7: fixed
  P1.8: skipped
  P2.1: skipped
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
---

# Verification Review: Artifact Views Fixes

## Review Report

**Review mode**: light (`mode:verify`)
**Parent review**: `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md`
**Files reviewed**: current changed-file scope, excluding generated `.cg-docs/views/**` bodies and diffs
**Findings**: 15 (P0: 2, P1: 8, P2: 5, P3: 0)

The required parent review is the newest eligible standard review with explicitly
fixed findings. Its fixed scope concerns WB report-writing contracts and does not
cover the artifact-view implementation. Therefore no current P2/P3 finding was
suppressed. P0/P1 and cross-file breakage are always reportable.

The artifact-view fix ledger in
`.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-verify-review-4.md`
was supplied as context only. Reviewers verified the actual code rather than
trusting its fixed/skipped statuses.

## P0 - BLOCKING

### P0.1 - Windows publication can overwrite a concurrently swapped target

- **Files**: `scripts/secure_fs.py:424-455`,
  `scripts/artifact_views/tests/test_writer.py:177`
- **Why**: The Windows writer captures existing metadata only for mode selection,
  then performs a replacing handle rename after the test hook without verifying
  the destination file identity. It then applies mode through pathname-based
  `chmod`. A concurrent user file can be replaced or have its mode changed.
- **Fix**: Bind target identity and mode changes to verified handles/file IDs,
  fail closed on a target swap, and add a Windows target-swap test that preserves
  the concurrent user file.

### P0.2 - POSIX stale-file rollback can overwrite a newly created file

- **Files**: `scripts/secure_fs.py:368-418`,
  `scripts/tests/test_target_ownership.py:249`
- **Why**: Checksum-mismatch and final rollback paths use replacing
  `os.replace(quarantine, name)`. If another actor creates a new file at the
  original name after quarantine, rollback silently destroys it.
- **Fix**: Restore without replacement; if the original name is occupied,
  preserve both the new file and quarantine and fail loudly. Add a
  post-quarantine collision test and equivalent Windows deletion coverage.

## P1 - CRITICAL

### P1.1 - Both generated artifact views are stale

- **Files**: `.cg-docs/brainstorms/2026-07-31-dual-audience-workflow-artifact-rendering.md`,
  `.cg-docs/plans/2026-07-31-dual-audience-workflow-artifact-views-v2.md`
- **Why**: Both supplied `cg-render-artifact --check` commands return `stale`
  with exit code 1. The required commit/PR freshness gate therefore fails.
- **Fix**: After resolving review findings, regenerate both mirrored views and
  require `--check` to return `current` with exit code 0.

### P1.2 - New files still override restrictive process umasks

- **Files**: `scripts/secure_fs.py:292-321`, `scripts/secure_fs.py:863-869`,
  `scripts/artifact_views/tests/test_writer.py`
- **Why**: The fix explicitly forces `0644` or `0755` for new files. Under a
  process `umask 077`, this broadens permissions beyond the caller's policy.
  Existing tests run under the ambient umask and cannot detect this regression.
- **Fix**: Let creation umask govern new-file modes, preserve exact mode only for
  replacements, and add a POSIX test that sets/restores `umask(0o077)`.

### P1.3 - Secure cleanup ends with pathname-based directory pruning

- **Files**: `scripts/cg_generate_targets.py:1157-1192`
- **Why**: After secure deletion closes pinned handles, `_prune_empty_parents()`
  uses `Path.rmdir()`. A swapped ancestor can redirect optional cleanup outside
  the generated target root.
- **Fix**: Prune through no-follow descriptor-relative operations or omit this
  optional cleanup.

### P1.4 - View-body exclusions remain vulnerable to hard links and read races

- **Files**: `scripts/brain/scanner.py:84-143`,
  `scripts/cg_audit_context.py:386-412`
- **Why**: Symlink checks do not detect hard-link aliases, and path checks occur
  separately from `read_text()`. A view body can be aliased or swapped into an
  allowed path before reading.
- **Fix**: Open once with no-follow/pinned semantics, validate the opened
  identity, and reject inode/file-ID aliases of excluded view files.

### P1.5 - Design evidence is still self-attested

- **Files**: `scripts/artifact_views/evidence.py:124-198`,
  `scripts/artifact_views/tests/test_evidence.py:42-72`
- **Why**: Screenshots and PDFs need only be nonempty; tests still accept literal
  `b"png"` and `b"pdf"`. Dimensions, signatures, evidence hashes,
  source-view provenance mapping, and machine origins of booleans are not
  validated.
- **Fix**: Validate media signatures/dimensions/hashes, source-view provenance,
  and structured machine-produced measurement artifacts.

### P1.6 - Non-string status/deviation values bypass enum validation

- **Files**: `scripts/artifact_views/validator.py:195-241`
- **Why**: Typed values such as booleans or integers satisfy required-field
  checks, are converted to an empty string, and avoid enum rejection.
- **Fix**: Require status and deviation policy to be strings before membership
  checks; parameterize booleans, integers, lists, and null cases.

### P1.7 - Indented fenced examples can still satisfy step metadata

- **Files**: `scripts/artifact_views/parser.py:520-534`,
  `scripts/artifact_views/parser.py:781-803`
- **Why**: `_consume_list()` can absorb an indented fence into a list block, and
  `_extract_label()` searches the whole raw block. Fake Requirements or Tests
  labels inside the nested example are accepted.
- **Fix**: Parse metadata only from documented top-level list-item lines and add
  nested-fence regressions.

### P1.8 - Plan validation remains ordered before the real save operation

- **Files**: `.github/prompts/cg-plan.prompt.md:162-210`,
  `tests/prompt-tools.Tests.ps1:6246-6249`, generated target commands
- **Why**: Validation instructions still precede the approved `**Save:**` block.
  The existing Pester assertion anchors an earlier generic “Write the plan”
  phrase, so it passes despite incorrect ordering.
- **Fix**: Move validation immediately after the exact save operation, anchor the
  test to `**Save:**`, and regenerate all native targets.

## P2 - IMPORTANT

### P2.1 - CI and release gates omit critical suites and Python 3.8 execution

- **Files**: `.github/workflows/tests.yml`, `create-release.ps1`
- **Why**: Artifact-view, evidence, Brain scanner, and summary suites are absent
  from merge/release automation. CI runs only Python 3.11 despite advertised
  Python 3.8 support.
- **Fix**: Add the required suites on Windows/macOS and a Python 3.8 matrix job;
  include the same suites in release preflight.

### P2.2 - Public API documentation coverage is incomplete

- **Files**: `scripts/tests/test_target_documentation.py:189-202`,
  `scripts/artifact_views/provenance.py:173-195`, `scripts/secure_fs.py:226-259`
- **Why**: The test inspects only top-level functions under
  `scripts/artifact_views/`; it misses public methods and shared public APIs.
- **Fix**: Walk the full AST, including class methods and touched shared modules.

### P2.3 - CMD/version/uninstall runtime parity is mostly static

- **Files**: `tests/install.Tests.ps1:633`, Python-backed CMD launchers,
  Windows uninstall path
- **Why**: Only `cg-render-artifact.cmd` receives a failing-child runtime test.
  No executed test covers sibling exit propagation, Python 3.7-to-3.8 fallback,
  or Windows uninstall. On non-Windows hosts the file reports a dummy pass.
- **Fix**: Parameterize runtime tests across all four CMD launchers and execute
  uninstall in an isolated Windows fixture; report platform absence as skips.

### P2.4 - Plan status vocabulary invariant is tautological

- **Files**: `scripts/artifact_views/tests/test_contract.py:168-203`
- **Why**: `PLAN_STATUSES` is compared with another hardcoded set instead of a
  documented owner, so prose drift remains invisible.
- **Fix**: Define or extract a canonical documented Plan-status list and compare
  it exactly with executable constants.

### P2.5 - The single-pass tokenizer test does not prove linear scaling

- **Files**: `scripts/artifact_views/tests/test_security.py:141`
- **Why**: The test only searches the top-level function for `.find()`. Moving
  quadratic work into a helper would pass.
- **Fix**: Add deterministic work-count or input-growth assertions that include
  helpers.

## Passed

- Both review agents produced usable, file-grounded output.
- Exact-byte freshness correctly detects the supplied stale views.
- Lossless table validation, scope/Required checks, charterless roots,
  symlink exclusions, POSIX uninstall ownership, nested-list raw fallback, and
  source reconstruction retained coverage.
- No generated `.cg-docs/views/**` body or diff was read.

## Verification Result

The cycle has **not converged**. No fixes were applied in verification mode.
Resolve P0/P1 findings, regenerate stale views through an authorized workflow,
and rerun `/cg-review mode:verify`.
