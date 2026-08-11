---
date: 2026-08-11
depth: full
type: standard
plan: null
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P3.1: fixed
  P3.2: skipped
  P3.3: skipped
---

# Review: Kilo Agent Parsing Failure — Windows Linker copy-directory Fix

## Review Report

**Review mode**: full
**Files reviewed**: 3 (`scripts/link.ps1`, `tests/link.Tests.ps1`, `scripts/tests/test_target_mapping.py`)
**Findings**: 14 (P1: 1, P2: 10, P3: 3)

### Background

Root cause of the recurring "Failed to parse agent" errors: Windows `link.ps1` creates
junctions to an external Compound GPID install for `.kilo/` units; Kilo rejects
markdown agents resolvable outside the project root. The change implements a
checksum-managed `copy-directory` strategy for Windows so Kilo units are
project-local copies. All 10 review agents ran (code-quality, testing, documentation,
version-control, reproducibility, performance, architecture, data-quality,
learnings-researcher, adversarial).

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality, cg-code-quality] `scripts/link.ps1:189` — malformed-but-parseable managed-copy marker crashes the entire link run.
  **Why**: `$data.schemaVersion` / `[string]$data.source` are read outside the `try/catch`; under `Set-StrictMode -Version Latest` a marker of `{}`, `[]`, or with missing keys throws `PropertyNotFoundException` (terminating with `$ErrorActionPreference="Stop"`), aborting all platform linking and also firing from `Get-CgInstalledGitignoreEntries`. This defeats the function's stated "invalid marker → warn and preserve" contract.
  **Fix**: Guard the marker root as a `PSCustomObject` and defend every field read inside a try that returns `$null` (preserve) on failure; reject arrays and non-object roots.
  **tags**: [safe_auto]

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-reproducibility] `scripts/helpers.ps1:356` — `Get-CgFileSha256` uses wildcard `-Path` binding, not `-LiteralPath`.
  **Why**: Filenames containing `[`, `]`, `*`, `?` hash as `$null` (verified), breaking checksum-gated copy/preserve/delete decisions that the whole feature relies on.
  **Fix**: Use `Test-Path -LiteralPath` and `Get-FileHash -LiteralPath`.
  **tags**: [safe_auto]

- **[P2.2]** [cg-data-quality] `scripts/link.ps1:194-207` — `files` member never schema-validated.
  **Why**: Non-object `files` values inject bogus entries (e.g. `Length`/`Count`), checksum values are unvalidated, and an empty `files:{}` marker is accepted as valid, silently un-managing previously tracked files.
  **Fix**: Require `files` to be an object; reject keys equal to the marker name; require values to match `^[0-9a-fA-F]{64}$`; reject → `$null` (preserve) on any violation.
  **tags**: [safe_auto]

- **[P2.3]** [cg-version-control] `scripts/link.ps1:29,210-249` — `.compound-gpid-managed-copy.json` marker files are not gitignored.
  **Why**: When `link.ps1` runs against the compound-gpid repo itself (tracked `.kilo/`/`.claude/`/`.agents/`/`.opencode/`), markers land as untracked files that can be committed as generated-tree drift.
  **Fix**: Add `**/.compound-gpid-managed-copy.json*` to the root `.gitignore` (covers `.tmp-*`/`.bak-*` siblings).
  **tags**: [safe_auto]

- **[P2.4]** [cg-documentation] `scripts/link.ps1` — security-critical functions lack explanatory comments.
  **Why**: The sync write-preserve policy, the `Resolve-CgContainedCopyPath` threat model, the `Read-…` `$null` contract, and `Adopt-…` all-or-nothing semantics are non-obvious and a maintainer could "fix" them incorrectly.
  **Fix**: Add header/inline comments documenting write policy (write if absent / byte-identical to source / byte-identical to previous managed; otherwise preserve), the traversal defense, the `$null ⇒ unmanaged/skipped` contract, atomic-replace intent, and the ancestor-reparse walk.
  **tags**: [safe_auto]

- **[P2.5]** [cg-architecture] `scripts/unlink.ps1:50-66` — unlink has no `copy-directory` removal path.
  **Why**: A link+unlink cycle leaves a stale local `.kilo/` mirror tree and marker on disk, now unprotected by `.gitignore`.
  **Fix**: Extend unlink to remove checksum-verified managed copied files and the marker, preserving user-modified files.
  **tags**: [manual]

- **[P2.6]** [cg-reproducibility, cg-data-quality] `scripts/link.ps1:251-277` — exact-match-only adoption silently skips pre-existing real directories.
  **Why**: Any single divergent/user-edited file makes `Adopt` return `$null`; the unit is then skipped forever (never synced, no marker, no gitignore entry) — a stuck state without a repair path.
  **Fix**: Adopt at per-file granularity (mark matching files, preserve+skip user-owned ones), consistent with `Sync` semantics.
  **tags**: [manual]

- **[P2.7]** [cg-performance] `scripts/link.ps1:426-450` — adopt-then-sync performs a full second re-hash/enumeration and double marker write.
  **Why**: Adopt only returns non-null when the tree is byte-identical, so the subsequent full Sync adds no information (~2x hashing and enumeration on the migration path).
  **Fix**: Skip `Sync` when the manifest came from a successful `Adopt` (or pass precomputed hashes through).
  **tags**: [manual]

- **[P2.8]** [cg-architecture] `scripts/link.sh:252-254` vs `scripts/link.ps1` — same `copy-directory` strategy now has divergent behavioral guarantees (Windows preserves user edits, macOS/Linux overwrites them).
  **Why**: `link.sh` uses blind `cp -R`; the marker is Windows-only, so platform state is not interoperable.
  **Fix**: Align implementations or explicitly document that preservation is a Windows-only reinforcement.
  **tags**: [manual]

- **[P2.9]** [cg-architecture, cg-code-quality] `scripts/link.ps1:122-168` — duplicated path-safety primitives vs `scripts/helpers.ps1:406-437` (`Resolve-CgContainedPath`, `Test-CgReparsePath`).
  **Why**: Path-containment policy now lives in two files with different rules; a hardening to one can leave the other weak.
  **Fix**: Consolidate into helpers and route link.ps1 through them, with unit tests.
  **tags**: [manual]

- **[P2.10]** [cg-architecture] `scripts/link.ps1:176-208,428-435,558-561` — a marker rejected for one bad key silently un-manages the whole directory and drops its `.gitignore` entry, with no recovery path.
  **Why**: The fail-loudly→skip-and-forget failure mode leaves already-managed content unmanaged, un-ignored, and stale.
  **Fix**: Reject bad keys individually (manage the rest) or retain the `.gitignore` entry while warning; add a repair path.
  **tags**: [manual]

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-performance] `scripts/link.ps1:299` — source checksum computed before the cheap reparse/conflict guards in `Sync`, so skipped files are hashed for nothing.
  **Why**: Reorder so `Test-CgCopyPathHasReparsePoint`/`Get-Item` run before hashing; behavior-neutral.
  **tags**: [safe_auto]

- **[P3.2]** [cg-reproducibility] `scripts/link.ps1:224-231,359` — marker `files` key order is hash-bucket order (not stable) and the marker is rewritten unconditionally each run.
  **Why**: Byte-level nondeterminism + churn; users tracking `.kilo/*` see marker diffs after every relink.
  **Fix**: Sort keys before serialization and skip the write when `files` is unchanged.
  **tags**: [advisory]

- **[P3.3]** [cg-documentation, cg-version-control, cg-architecture] test/style/documentation nits.
  **Why**: 4-space vs 8-space indentation in `tests/link.Tests.ps1:484-494`; the replica regex comment in `tests/link.Tests.ps1:396` is stale vs production; `scripts/tests/test_target_mapping.py:123` uses a different loader idiom; new marker absent from `docs/reference/files.md`; marker name `/`schema convention diverges from `managed-copy`; `Test-CgOwnedJunction` in link vs unlink now intentionally diverge without comment.
  **Fix**: Re-indent; update the replica comment; unify loader; document marker.
  **tags**: [advisory]

### ✅ Passed

- cg-adversarial: no unresolved P0/P1 (marker reparse/atomic-write safety and test junction cleanup verified resolved)
- cg-testing: no unresolved P0/P1; behavioral coverage added for migration, preservation, and traversal rejection
- Path containment, exact-target junction ownership, atomic marker write, no-BOM `.gitignore`, `$Args`→`$Arguments` rename: verified correct across agents

---

**Review mode**: full
**Files reviewed**: 3
**Findings**: 14 (P0: 0, P1: 1, P2: 10, P3: 3)
